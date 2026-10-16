"""Emit parallel M1 arithmetic for the audited8357 semantic instruction-cost plans.

This is specific to audio_note_sequence_cost.py,not a general T-state->M1 rule.
Its8T nodes are CB instructions;14/15/19/20/23T nodes are indexed instructions;
16T nodes are LDI. Three explicit12T BIT(HL) sites override the JR default.
F3's -16T adjustment removes two ordinary fetches.
Duration multiplication is an aggregate and receives its explicit loop count.
No ROM instruction is decoded or interpreted by the emitted semantic model.
"""
import ast,copy,hashlib
from actor_reference import ROOT

FETCHES={0:0,4:1,5:1,6:1,7:1,8:2,10:1,11:1,12:1,13:1,14:2,15:2,16:2,17:1,19:2,20:2,23:2}
AUDITED_SHA='9d221240da595448c0e70d23f0f44475ccf23fdbecc93f98761cc880f8e482f8'
BIT_HL_PLANS={32:'12 + 10 + 12',39:'7 + 10 + 12 + 10',98:'7 + 10 + 12'}
def fetch(node):
 if isinstance(node,ast.Constant):return ast.Constant(FETCHES[node.value])
 if isinstance(node,ast.Name):return ast.Name({'cost':'m1','work':'work_m1','POINTER_COST':'POINTER_M1'}[node.id],ast.Load())
 if isinstance(node,ast.BinOp):
  if isinstance(node.op,ast.Mult):
   assert isinstance(node.left,ast.Constant)
   return ast.BinOp(copy.deepcopy(node.left),ast.Mult(),fetch(node.right))
  assert isinstance(node.op,(ast.Add,ast.Sub));return ast.BinOp(fetch(node.left),copy.deepcopy(node.op),fetch(node.right))
 if isinstance(node,ast.IfExp):return ast.IfExp(copy.deepcopy(node.test),fetch(node.body),fetch(node.orelse))
 if isinstance(node,ast.Call):
  assert isinstance(node.func,ast.Name) and node.func.id=='sum' and len(node.args)==1 and isinstance(node.args[0],ast.List)
  return ast.Call(ast.Name('sum',ast.Load()),[ast.List([fetch(e) for e in node.args[0].elts],ast.Load())],[])
 raise ValueError(ast.dump(node))

class Emit(ast.NodeTransformer):
 def visit_Assign(self,node):
  node=self.generic_visit(node)
  if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='cost':return [node,ast.Assign([ast.Name('m1',ast.Store())],fetch(node.value))]
  if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='multiply':
   assert len(node.targets)==1 and isinstance(node.targets[0],ast.Tuple);node.targets[0].elts.append(ast.Name('work_m1',ast.Store()))
  return node
 def visit_AugAssign(self,node):
  node=self.generic_visit(node)
  if isinstance(node.target,ast.Name) and node.target.id=='cost':
   counted=fetch(node.value)
   if node.lineno in BIT_HL_PLANS:
    assert ast.unparse(node.value)==BIT_HL_PLANS[node.lineno]
    counted=ast.BinOp(counted,ast.Add(),ast.Constant(1)) #CB7E BIT7,(HL):two fetches.
   return [node,ast.AugAssign(ast.Name('m1',ast.Store()),copy.deepcopy(node.op),counted)]
  return node
 def visit_Return(self,node):
  if isinstance(node.value,ast.Tuple):
   assert len(node.value.elts)==2;node.value.elts.append(ast.Call(ast.Name('_duration_m1',ast.Load()),[ast.Name('scale',ast.Load())],[]));return node
  if not (isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='dict'):return node
  cost=next(k.value for k in node.value.keywords if k.arg=='tstates');node.value.keywords.append(ast.keyword('m1_fetches',fetch(cost)));return node

def main():
 path=ROOT/'tools/audio_note_sequence_cost.py';source=path.read_bytes();tree=ast.parse(source)
 assert hashlib.sha256(source).hexdigest()==AUDITED_SHA,'Reaudit instruction annotations before regenerating'
 function=next(n for n in tree.body if isinstance(n,ast.FunctionDef));function=Emit().visit(function);function.name='note_sequence_refresh';ast.fix_missing_locations(function)
 header='"""Generated8357 semantic state/cost/M1 model;see generate_note_sequence_refresh.py."""\n'
 header+=f'# Cost-plan SHA256: {hashlib.sha256(source).hexdigest()}\nfrom audio_dispatch_cost import POINTER_COST\nPOINTER_M1=9\ndef _duration_m1(scale):return 4 if scale==1 else 6+2*((scale-1)&255)\n\n'
 (ROOT/'tools/audio_note_sequence_refresh.py').write_text(header+ast.unparse(function)+'\n')
 print('8357 semantic M1 plan emitted from audited instruction-cost expressions.')
if __name__=='__main__':main()
