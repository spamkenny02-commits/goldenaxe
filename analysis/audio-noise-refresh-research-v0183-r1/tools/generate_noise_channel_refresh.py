"""Emit864F M1 composition;dispatcher/duration aggregates have explicit fetch plans."""
import ast,hashlib,copy
from actor_reference import ROOT
from generate_tone_channel_refresh import Tone,tone_fetch

AUDITED_SHA='0f5c3aad31c5cf57a8f1de409d6adaed5d1d5ff53d2d0da30d2a85ea13fa644a'
def noise_fetch(node):
 if isinstance(node,ast.Constant) and node.value in [109,18]:return ast.Constant({109:15,18:2}[node.value])
 if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id=='helper':
  assert isinstance(node.slice,ast.Constant) and node.slice.value=='tstates';return ast.Subscript(copy.deepcopy(node.value),ast.Constant('m1_fetches'),ast.Load())
 if isinstance(node,ast.IfExp):
  if isinstance(node.body,ast.Constant) and node.body.value==34:
   assert ast.unparse(node.test)=='scale == 1';return ast.Call(ast.Name('_duration_m1',ast.Load()),[ast.Name('scale',ast.Load())],[])
  return ast.IfExp(copy.deepcopy(node.test),noise_fetch(node.body),noise_fetch(node.orelse))
 if isinstance(node,ast.BinOp):return ast.BinOp(noise_fetch(node.left),copy.deepcopy(node.op),noise_fetch(node.right))
 return tone_fetch(node)

class Noise(Tone):
 def visit_Name(self,node):
  if node.id=='noise_note_cost':node.id='noise_note_refresh'
  return super().visit_Name(node)
 def visit_AugAssign(self,node):
  node=self.generic_visit(node)
  if isinstance(node.target,ast.Name) and node.target.id=='cost':return [node,ast.AugAssign(ast.Name('m1',ast.Store()),copy.deepcopy(node.op),noise_fetch(node.value))]
  return node

def main():
 source=(ROOT/'tools/audio_noise_channel_cost.py').read_bytes();assert hashlib.sha256(source).hexdigest()==AUDITED_SHA,'Reaudit noise instruction annotations'
 function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef));function=Noise().visit(function);function.name='noise_channel_refresh';ast.fix_missing_locations(function)
 header='"""Generated864F semantic state/cost/M1 composition;see generate_noise_channel_refresh.py."""\n'
 header+=f'# Cost-plan SHA256: {AUDITED_SHA}\nfrom audio_noise_note_refresh import noise_note_refresh\nfrom audio_envelope_refresh import adsr_refresh,table_envelope_refresh\nfrom audio_note_sequence_refresh import _duration_m1\n\n'
 (ROOT/'tools/audio_noise_channel_refresh.py').write_text(header+ast.unparse(function)+'\n');print('864F M1 composition emitted from audited plans andsemantic submodels.')
if __name__=='__main__':main()
