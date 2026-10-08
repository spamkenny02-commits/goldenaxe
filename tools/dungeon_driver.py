"""Read-only dungeon navigation; every action is a joypad button.

Routes use checked room identities and explicit stair targets. The driver
plans on the live descriptor buffer, waits for real gates, and attacks actual
enemies rather than changing collision, health or progression RAM.
"""
from heapq import heappop, heappush


class DungeonDriver:
    def __init__(self, route, read, buttons):
        self.route, self.read, self.buttons = route, read, buttons
        self.stage = 'entry'
        self.edge = 0
        self.target = None
        self.path_key = None
        self.path = []
        self.visits = []
        self.last_cell = None
        self.done = False
        self.events = []
        self.actions_done = set()
        self.item = 0
        self.breaking = None
        self.thunder_cells = {}
        self.escaping = False
        self.last_mp = None

    def pad(self, direction):
        return 1 << self.buttons[direction]

    def desired_item(self):
        # Using a consumable refreshes the HUD and selects the sword. Do not
        # reopen inventory for an antidote that has just been consumed.
        if self.item==2 and (not self.read(0xC0BF) or not self.read(0xC0E2)):
            self.item=0
        return 1 if self.item==0 and self.route.get('index',0)>=9 and not self.escaping else self.item

    def evade(self, grabbers):
        """Choose a reachable escape instead of pushing into a nearby wall."""
        x,y=self.read(0xC313),self.read(0xC311)
        candidates=[]
        for dx,dy in ((0,-32),(0,32),(-32,0),(32,0)):
            goal=(max(24,min(232,round(x/8)*8+dx)),
                  max(24,min(144,round(y/8)*8+dy)))
            self.navigate(goal)
            if self.breaking:
                self.breaking=None
                continue
            if self.path and self.path[-1]==goal:
                separation=min(abs(tx-goal[0])+abs(ty-goal[1]) for tx,ty in grabbers)
                candidates.append((separation,-len(self.path),goal))
        if not candidates:return 0
        return self.navigate(max(candidates,key=lambda c:c[:2])[2])

    def boss_melee(self):
        """Approach an axis of the large boss rather than its center."""
        r=self.read
        x,y=r(0xC313),r(0xC311)
        tx,ty=r(0xC613),r(0xC611)
        dx,dy=tx-x,ty-y
        if r(0xC301) in (2,3,4,5):return 0
        if r(0xC605)>0:
            return self.evade([(tx,ty)]) if abs(dx)+abs(dy)<56 else 0
        if (abs(dx)<=4 and 24<=abs(dy)<=32) or (abs(dy)<=4 and 24<=abs(dx)<=32):
            direction=('right' if dx>0 else 'left') if abs(dx)>abs(dy) else ('down' if dy>0 else 'up')
            facing={'up':0,'down':1,'left':2,'right':3}[direction]
            if r(0xC30A)!=facing:return self.pad(direction)
            return self.pad('button2') if not r(0xC020)&32 else 0
        candidates=[]
        for ox,oy in ((0,-32),(32,0),(0,24),(-24,0)):
            goal=(round((tx+ox)/8)*8,round((ty+oy)/8)*8)
            if not 24<=goal[0]<=232 or not 24<=goal[1]<=144:continue
            pad=self.navigate(goal,attack=True)
            if self.breaking:
                self.breaking=None;continue
            if self.path and self.path[-1]==goal:
                candidates.append((len(self.path),goal))
        if candidates:return self.navigate(min(candidates)[1],attack=True)
        return self.evade([(tx,ty)])

    def navigate(self, target, attack=False):
        r = self.read
        x, y = r(0xC313), r(0xC311)
        if self.breaking:
            tile,direction=self.breaking
            if r(0xDC00+tile) not in (0x0B,0x31):
                self.breaking=None;self.item=0;self.path_key=None;return 0
            self.item=5
            if r(0xC0DF)!=5 or r(0xC301)!=1:return 0
            if r(0xC0DB)<8:
                self.breaking=None;self.item=0;self.path_key=None
            else:
                if r(0xC30A)!={'up':0,'down':1,'left':2,'right':3}[direction]:return self.pad(direction)
                return self.pad('button2') if not r(0xC020)&32 else 0
        if r(0xC304):return 0
        # Positions advance by substeps. Finish the chosen eight-pixel step.
        if self.target and (x,y)!=self.target and (x | y) & 7:
            tx, ty = self.target
            return self.pad('right' if x < tx else 'left') if x!=tx else self.pad('down' if y < ty else 'up')
        start = (round(x/8)*8, round(y/8)*8)
        goal = tuple(target)
        grid = bytes(r(0xD600+i) for i in range(1536))
        cell=r(0xC0B9)|r(0xC0BA)<<8
        terrain_context=(cell,bool(r(0xC0EC)),bool(r(0xC0F0)),r(0xC0DB)>=8)
        hazards=() if attack else tuple((r(0xC313+s*48),r(0xC311+s*48))
            for s in range(16,24) if 32<=r(0xC300+s*48)<99
            and r(0xC303+s*48)&3==3 and r(0xC300+s*48)!=94)
        key = (start, goal, grid, terrain_context, hazards)
        if key != self.path_key:
            self.path_key = key
            def allowed(point, delta):
                px, py = point
                nx, ny = px+delta[0], py+delta[1]
                if [nx,ny] in self.route.get('avoid',{}).get(str(cell),[]) and (nx,ny)!=goal:return False
                if not 8 <= nx <= 248 or not 8 <= ny <= 168:return False
                if (nx < 16 or nx > 240 or ny < 16 or ny > 160) and (nx,ny) != goal:return False
                probes = {(0,-8):((-4,-12),(4,-12)),(0,8):((-4,4),(4,4)),(-8,0):((-12,-4),),(8,0):((12,-4),)}[delta]
                def high_at(dx,dy):
                    off=((((py+dy)&255)&248)<<3)+((((px+dx)&255)>>2)&62)+1
                    return grid[off] if off<len(grid) else 0x80
                boots = high_at(-4,-4)&high_at(4,-4)&0xC0 if r(0xC0F0) else 0
                move_cost=1
                for dx, dy in probes:
                    off = ((((py+dy)&255)&248)<<3) + ((((px+dx)&255)>>2)&62) + 1
                    high = grid[off] if off < len(grid) else 0x80
                    if not r(0xC0EC) and high&0x20:high|=0x80
                    if boots&0x40:
                        if high&0x40:high&=~0x80
                        elif boots&0x80:high|=0x80
                    door_approach = (delta==(0,-8) and 112<=px<=144 and 24<=py<=40) or (delta==(-8,0) and px<=32 and 64<=py<=88) or (delta==(8,0) and px>=224 and 64<=py<=88)
                    tile=r(0xDC00+((py+dy)//16)*16+(px+dx)//16)
                    if high&0x80 and (not r(0xC0BA) or r(0xC0DB)<8 or tile not in (0x0B,0x31)) and not (high&0xE0==0xA0 and door_approach):return False
                    if high&0x80 and tile in (0x0B,0x31):move_cost=16
                if hazards:
                    distance=min(abs(hx-nx)+abs(hy-ny) for hx,hy in hazards)
                    if distance<24:move_cost+=24
                    elif distance<40:move_cost+=8
                return move_cost
            queue = [(0,start)]; parents = {start: None}; costs={start:0}
            best = start
            while queue:
                cost,point = heappop(queue)
                if cost!=costs[point]:continue
                if abs(point[0]-goal[0])+abs(point[1]-goal[1]) < abs(best[0]-goal[0])+abs(best[1]-goal[1]): best = point
                if point == goal: best = point; break
                for dx, dy in ((0,-8),(0,8),(-8,0),(8,0)):
                    nxt = (point[0]+dx, point[1]+dy)
                    move_cost=allowed(point,(dx,dy))
                    if move_cost:
                        new_cost=cost+move_cost
                        if new_cost<costs.get(nxt,10**9):
                            costs[nxt]=new_cost;parents[nxt]=point;heappush(queue,(new_cost,nxt))
            path = []
            while parents[best] is not None:
                path.append(best); best = parents[best]
            self.path = list(reversed(path))
        if self.path:
            self.target = self.path[0]
        else:
            self.target = goal
        tx, ty = self.target
        direction=('right' if x<tx else 'left') if x!=tx else ('down' if y<ty else 'up') if y!=ty else None
        if direction is None:self.item=0;return 0
        probes={'up':((-4,-12),(4,-12)),'down':((-4,4),(4,4)),'left':((-12,-4),),'right':((12,-4),)}[direction]
        for dx,dy in probes:
            tile=((y+dy)//16)*16+(x+dx)//16
            if r(0xC0BA) and r(0xC0DB)>=8 and r(0xDC00+tile) in (0x0B,0x31):
                self.breaking=(tile,direction);self.item=5;return 0
        self.item=0
        return self.pad(direction)

    def drive(self, state, boss_done):
        r = self.read
        cell = r(0xC0B9) | r(0xC0BA)<<8
        if state != 0x0C:return 0
        mp=r(0xC0DB)
        if self.last_mp is not None and mp!=self.last_mp:
            self.events.append({'mp_before':self.last_mp,'mp_after':mp,'cell':cell,'item':r(0xC0DF),'player_state':r(0xC301),'effect':r(0xC090),'enemies':[[r(0xC300+s*48),r(0xC318+s*48),r(0xC303+s*48)] for s in range(16,24)]})
        self.last_mp=mp
        if r(0xC301)==12:
            # Type 91 releases its grab after six new direction presses.
            self.escaping=True;self.breaking=None;self.item=0
            return self.pad('left') if not r(0xC020)&4 else self.pad('right')
        if self.escaping:
            self.item=0
            if r(0xC0DF)!=0 or r(0xC301)==0:return 0
            x,y=r(0xC313),r(0xC311)
            grabbers=[(r(0xC313+s*48),r(0xC311+s*48)) for s in range(16,24) if r(0xC300+s*48)==91 and r(0xC318+s*48)]
            if grabbers:
                tx,ty=min(grabbers,key=lambda p:abs(p[0]-x)+abs(p[1]-y))
                if abs(tx-x)+abs(ty-y)<24:
                    # Retreat before attacking. Killing a still attached
                    # grabber can leave the hero trapped even in the original.
                    return self.evade(grabbers)
            self.escaping=False
        # Late rooms contain several curse casters. Cure only after they
        # are gone, so the single antidote is not immediately invalidated.
        cure_ready=self.route.get('index',0)<9 or (cell!=0x1FD and not any(
            r(0xC300+s*48)==83 and r(0xC318+s*48)>0 for s in range(16,24)))
        if r(0xC0BF) and r(0xC0E2) and cure_ready:
            self.item=2
            if r(0xC0DF)!=2 or r(0xC301)!=1:return 0
            return self.pad('button2') if not r(0xC020)&32 else 0
        if self.last_cell != cell:
            self.visits.append({'cell': cell, 'stage': self.stage, 'index': r(0xC037)})
            self.last_cell = cell; self.target = None; self.path_key = None
        if self.stage == 'entry':
            if cell == self.route['entrance']:
                assert r(0xC037) == self.route['index'], 'Dungeon entry did not assign its index'
                self.stage = 'outbound'; self.edge = 0
                self.events.append('entered')
            else:return self.navigate(self.route['entry_target'])
        if self.stage == 'boss':
            if not boss_done:return None
            self.events.append('reward_complete'); self.stage = 'return'; self.edge = 0
        if self.stage in ('outbound','return'):
            edges = self.route[self.stage]
            expected_arrival=self.edge<len(edges) and cell==edges[self.edge]['to']
            if self.edge and not expected_arrival and cell==edges[self.edge-1]['from']:
                self.edge-=1;self.target=None;self.path_key=None
                self.events.append({'retreated_to':cell})
            while self.edge < len(edges) and cell == edges[self.edge]['to']:
                self.events.append({'from':edges[self.edge]['from'],'to':cell,'stairs':edges[self.edge].get('stairs',False)})
                self.edge += 1; self.target = None; self.path_key = None
            if self.edge == len(edges):
                if self.stage == 'outbound':
                    self.stage = 'boss';return None
                self.stage = 'exit'
            else:
                edge = edges[self.edge]
                assert cell == edge['from'], f"Unexpected route cell {cell:03X}, expected {edge['from']:03X}"
                # Collect real drops before spending the limited magic reserve.
                x,y=r(0xC313),r(0xC311)
                drops=[(r(0xC313+s*48),r(0xC311+s*48)) for s in range(16,24)
                    if (r(0xC300+s*48)==12 and r(0xC0DB)<r(0xC0DC))
                    or (r(0xC300+s*48) in (10,11) and r(0xC318)<r(0xC0DA))]
                for tx,ty in sorted(drops,key=lambda p:abs(p[0]-x)+abs(p[1]-y)):
                    goal=(round(tx/8)*8,round(ty/8)*8)
                    pad=self.navigate(goal)
                    if self.breaking:self.breaking=None;continue
                    if self.path and self.path[-1]==goal:return pad
                puzzle=self.route.get('puzzles',{}).get(str(cell))
                trigger=r(0xC06E)
                if trigger<160 and r(0xDC00+trigger)==0x0B:
                    puzzle={'target':[(trigger%16)*16+8,(trigger//16)*16+24]}
                # With no MP, fight for real drops instead of casting an
                # unavailable spell forever at the trigger block.
                if puzzle and r(0xC0DB)>=8 and not r(0xC100+(cell&255))&4:
                    if [r(0xC313),r(0xC311)]!=puzzle['target']:return self.navigate(puzzle['target'])
                    self.item=5
                    if r(0xC0DF)!=5:return 0
                    if r(0xC30A)!=0:return self.pad('up')
                    return self.pad('button2') if not r(0xC020)&32 else 0
                action=self.route.get('actions',{}).get(str(cell))
                if action and cell not in self.actions_done:
                    if r(0xC100+(cell&255))&4:
                        self.actions_done.add(cell);self.events.append({'action':cell,'target':action})
                    elif [r(0xC313),r(0xC311)]==action:
                        return self.pad('up')
                    else:
                        action_pad=self.navigate(action)
                        if self.path and self.path[-1]==tuple(action):return action_pad
                # Real room-clear shutters must open through enemy deaths.
                enemies = [(r(0xC313+s*48),r(0xC311+s*48),r(0xC300+s*48)) for s in range(16,24) if (32<=r(0xC300+s*48)<99 or 120<=r(0xC300+s*48)<=124) and (r(0xC318+s*48)>0 or r(0xC300+s*48)==45) and r(0xC300+s*48)!=94]
                if r(0xC301) in (2,3,4,5) and self.route['index']>=9:
                    # Attack animation can rotate. Track the opposing shield
                    # facing throughout the swing, not just when it starts.
                    shield=[s for s in range(16,24) if r(0xC300+s*48) in (92,93)
                            and r(0xC318+s*48)>0]
                    if shield:
                        s=min(shield,key=lambda s:abs(r(0xC313+s*48)-x)+abs(r(0xC311+s*48)-y))
                        required=(1,0,3,2)[r(0xC30A+s*48)&3]
                        if r(0xC30A)!=required:return self.pad(('up','down','left','right')[required])
                    return 0
                if r(0xC301) in (2,3,4,5,10):return 0
                travel_pad=self.navigate(edge['target'])
                probe={'up':(128,24),'left':(16,72),'right':(232,72)}.get(edge.get('direction'))
                key_gate=probe and r(0xD600+((probe[1]&248)<<3)+((probe[0]>>2)&62)+1)&0xE0==0xA0
                if enemies and (r(0xC0A8)==1 or (not key_gate and (not self.path or self.path[-1]!=tuple(edge['target'])))):
                    x,y=r(0xC313),r(0xC311)
                    # Stop armor curses and grabs before ordinary melee targets.
                    tx,ty,kind=min(enemies,key=lambda p:(p[2] not in (83,91),abs(p[0]-x)+abs(p[1]-y)))
                    dx,dy=tx-x,ty-y
                    if self.route['index']>=9 and kind>=120:
                        slot=next(s for s in range(16,24) if r(0xC300+s*48)==kind)
                        if r(0xC305+slot*48)>8 and abs(dx)+abs(dy)<48:
                            return self.evade([(tx,ty)])
                    direction=('right' if dx>0 else 'left') if abs(dx)>abs(dy) else ('down' if dy>0 else 'up')
                    facing={'up':0,'down':1,'left':2,'right':3}[direction]
                    cross=abs(dx) if direction in ('up','down') else abs(dy)
                    if (kind==91 or (kind==83 and (r(0xC0DB)>=16 or r(0xC0C6)))) and abs(dx)+abs(dy)<32:
                        return self.evade([(ex,ey) for ex,ey,enemy in enemies if enemy in (83,91)])
                    def clear_shot():
                        for distance in range(8,max(abs(dx),abs(dy)),8):
                            sx=x+(distance if dx>0 else -distance) if direction in ('left','right') else x
                            sy=y+(distance if dy>0 else -distance) if direction in ('up','down') else y
                            high=r(0xD600+((sy&248)<<3)+((sx>>2)&62)+1)
                            if high&0xE0 in (0x80,0xA0):return False
                        return True
                    fire_reserve=16 if kind in (83,91) else 112
                    if abs(dx)+abs(dy)>=24 and cross<=8 and clear_shot() and (r(0xC0DB)>=fire_reserve or r(0xC0C6)) and not (self.route['index']==8 and cell==0x1DA):
                        self.item=4
                        if r(0xC0DF)!=4:return 0
                        if r(0xC30A)!=facing:return self.pad(direction)
                        pad=0
                        if not r(0xC020)&32:pad|=self.pad('button2')
                        return pad
                    if abs(dx)+abs(dy)<=20 and cross<=16:
                        self.item=1 if kind>=120 or self.route['index']>=9 else 0
                        if r(0xC0DF)!=self.item:return 0
                        if r(0xC30A)!=facing:return self.pad(direction)
                        pad=0
                        if not r(0xC020)&32:pad|=self.pad('button2')
                        return pad
                    pad=self.navigate([round(tx/8)*8,round(ty/8)*8],attack=True)
                    # A solid partition can put a room-clear enemy beyond
                    # melee and projectile reach. Thunder crosses the partition.
                    enemy_goal=(round(tx/8)*8,round(ty/8)*8)
                    # Fire crosses E0 partitions that block walking. Use it
                    # for an unreachable room-clear enemy even below the
                    # ordinary travel reserve (SMS 6, return room 113).
                    if self.stage=='return' and (not self.path or self.path[-1]!=enemy_goal) and not r(0xC304) and kind not in (83,91,45) and cross<=8 and clear_shot() and (r(0xC0DB)>=8 or r(0xC0C6)):
                        self.item=4
                        if r(0xC0DF)!=4:return 0
                        if r(0xC30A)!=facing:return self.pad(direction)
                        return self.pad('button2') if not r(0xC020)&32 else 0
                    vulnerable=all(not r(0xC318+s*48) or r(0xC303+s*48)&2 for s in range(16,24))
                    if (not self.path or self.path[-1]!=enemy_goal) and vulnerable and self.route['index']==8 and r(0xC0DB)>=32 and self.thunder_cells.get(cell,0)<3:
                        self.item=6
                        if r(0xC0DF)!=6 or r(0xC301)!=1 or r(0xC020)&32:return 0
                        self.thunder_cells[cell]=self.thunder_cells.get(cell,0)+1
                        return self.pad('button2')
                    return pad
                return self.navigate(edge['target'])
        if self.stage == 'exit':
            if cell == self.route['outside_cell']:
                assert r(0xC037)==0, 'Dungeon exit did not restore the world index'
                self.events.append('exited');self.done=True;return 0
            return self.navigate([128,160])
        return 0
