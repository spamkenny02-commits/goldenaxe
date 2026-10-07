"""Read-only dungeon navigation; every action is a joypad button.

Routes use checked room identities and explicit stair targets. The driver
plans on the live descriptor buffer, waits for real gates, and attacks actual
enemies rather than changing collision, health or progression RAM.
"""
from collections import deque


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

    def pad(self, direction):
        return 1 << self.buttons[direction]

    def navigate(self, target, attack=False):
        r = self.read
        x, y = r(0xC313), r(0xC311)
        if self.breaking:
            tile,direction=self.breaking
            if r(0xDC00+tile) not in (0x0B,0x31):
                self.breaking=None;self.item=0;self.path_key=None;return 0
            self.item=5
            if r(0xC0DF)!=5 or r(0xC301)!=1:return 0
            return self.pad(direction)| (self.pad('button2') if not r(0xC020)&32 else 0)
        if r(0xC304):return 0
        # Positions advance by substeps. Finish the chosen eight-pixel step.
        if self.target and (x,y)!=self.target and (x | y) & 7:
            tx, ty = self.target
            return self.pad('right' if x < tx else 'left') if x!=tx else self.pad('down' if y < ty else 'up')
        start = (round(x/8)*8, round(y/8)*8)
        goal = tuple(target)
        grid = bytes(r(0xD600+i) for i in range(1536))
        key = (start, goal, grid)
        if key != self.path_key:
            self.path_key = key
            def allowed(point, delta):
                px, py = point
                nx, ny = px+delta[0], py+delta[1]
                cell=r(0xC0B9)|r(0xC0BA)<<8
                if [nx,ny] in self.route.get('avoid',{}).get(str(cell),[]) and (nx,ny)!=goal:return False
                if not 8 <= nx <= 248 or not 8 <= ny <= 168:return False
                if (nx < 16 or nx > 240 or ny < 16 or ny > 160) and (nx,ny) != goal:return False
                probes = {(0,-8):((-4,-12),(4,-12)),(0,8):((-4,4),(4,4)),(-8,0):((-12,-4),),(8,0):((12,-4),)}[delta]
                def high_at(dx,dy):
                    off=((((py+dy)&255)&248)<<3)+((((px+dx)&255)>>2)&62)+1
                    return grid[off] if off<len(grid) else 0x80
                boots = high_at(-4,-4)&high_at(4,-4)&0xC0 if r(0xC0F0) else 0
                for dx, dy in probes:
                    off = ((((py+dy)&255)&248)<<3) + ((((px+dx)&255)>>2)&62) + 1
                    high = grid[off] if off < len(grid) else 0x80
                    if not r(0xC0EC) and high&0x20:high|=0x80
                    if boots&0x40:
                        if high&0x40:high&=~0x80
                        elif boots&0x80:high|=0x80
                    door_approach = (delta==(0,-8) and 112<=px<=144 and 24<=py<=40) or (delta==(-8,0) and px<=32 and 64<=py<=88) or (delta==(8,0) and px>=224 and 64<=py<=88)
                    tile=r(0xDC00+((py+dy)//16)*16+(px+dx)//16)
                    if high&0x80 and tile not in (0x0B,0x31) and not (high&0xE0==0xA0 and door_approach):return False
                return True
            queue = deque([start]); parents = {start: None}
            best = start
            while queue:
                point = queue.popleft()
                if abs(point[0]-goal[0])+abs(point[1]-goal[1]) < abs(best[0]-goal[0])+abs(best[1]-goal[1]): best = point
                if point == goal: best = point; break
                for dx, dy in ((0,-8),(0,8),(-8,0),(8,0)):
                    nxt = (point[0]+dx, point[1]+dy)
                    if nxt not in parents and allowed(point,(dx,dy)):
                        parents[nxt] = point; queue.append(nxt)
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
            if r(0xDC00+tile) in (0x0B,0x31):
                self.breaking=(tile,direction);self.item=5;return 0
        self.item=0
        return self.pad(direction)

    def drive(self, state, boss_done):
        r = self.read
        cell = r(0xC0B9) | r(0xC0BA)<<8
        if state != 0x0C:return 0
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
                puzzle=self.route.get('puzzles',{}).get(str(cell))
                trigger=r(0xC06E)
                if trigger<160 and r(0xDC00+trigger)==0x0B:
                    puzzle={'target':[(trigger%16)*16+8,(trigger//16)*16+24]}
                if puzzle and not r(0xC100+(cell&255))&4:
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
                    else:return self.navigate(action)
                # Real room-clear shutters must open through enemy deaths.
                enemies = [(r(0xC313+s*48),r(0xC311+s*48)) for s in range(16,24) if (32<=r(0xC300+s*48)<99 or 120<=r(0xC300+s*48)<=124) and (r(0xC318+s*48)>0 or r(0xC300+s*48)==45) and r(0xC300+s*48)!=94]
                if r(0xC301) in (2,3,4,5,10):return 0
                travel_pad=self.navigate(edge['target'])
                probe={'up':(128,24),'left':(16,72),'right':(232,72)}.get(edge.get('direction'))
                key_gate=probe and r(0xD600+((probe[1]&248)<<3)+((probe[0]>>2)&62)+1)&0xE0==0xA0
                if enemies and (r(0xC0A8)==1 or (not key_gate and (not self.path or self.path[-1]!=tuple(edge['target'])))):
                    x,y=r(0xC313),r(0xC311)
                    tx,ty=min(enemies,key=lambda p:abs(p[0]-x)+abs(p[1]-y))
                    dx,dy=tx-x,ty-y
                    direction=('right' if dx>0 else 'left') if abs(dx)>abs(dy) else ('down' if dy>0 else 'up')
                    facing={'up':0,'down':1,'left':2,'right':3}[direction]
                    cross=abs(dx) if direction in ('up','down') else abs(dy)
                    def clear_shot():
                        for distance in range(8,max(abs(dx),abs(dy)),8):
                            sx=x+(distance if dx>0 else -distance) if direction in ('left','right') else x
                            sy=y+(distance if dy>0 else -distance) if direction in ('up','down') else y
                            high=r(0xD600+((sy&248)<<3)+((sx>>2)&62)+1)
                            if high&0xE0 in (0x80,0xA0):return False
                        return True
                    if abs(dx)+abs(dy)>=24 and cross<=8 and clear_shot() and (r(0xC0DB)>=48 or r(0xC0C6)):
                        self.item=4
                        if r(0xC0DF)!=4:return 0
                        if r(0xC30A)!=facing:return self.pad(direction)
                        pad=0
                        if not r(0xC020)&32:pad|=self.pad('button2')
                        return pad
                    if abs(dx)+abs(dy)<24 and cross<=8:
                        self.item=0
                        if r(0xC0DF)!=0:return 0
                        if r(0xC30A)!=facing:return self.pad(direction)
                        pad=0
                        if not r(0xC020)&32:pad|=self.pad('button2')
                        return pad
                    return self.navigate([round(tx/8)*8,round(ty/8)*8])
                return self.navigate(edge['target'])
        if self.stage == 'exit':
            if cell == self.route['outside_cell']:
                assert r(0xC037)==0, 'Dungeon exit did not restore the world index'
                self.events.append('exited');self.done=True;return 0
            return self.navigate([128,160])
        return 0
