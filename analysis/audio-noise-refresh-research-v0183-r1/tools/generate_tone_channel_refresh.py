"""Emit84C7 M1 composition from audited instruction plans andsemantic submodels."""
import ast,copy,hashlib
from actor_reference import ROOT
from generate_note_sequence_refresh import Emit,fetch

AUDITED_SHA='a234f114d778c594e9129d3dae283498a3f62f473835fd0ea908dee39e32fd42'
HELPERS={'note_sequence_cost':'note_sequence_refresh','pitch_cost':'pitch_refresh','adsr_cost':'adsr_refresh','table_envelope_cost':'table_envelope_refresh'}
def tone_fetch(node):
 if isinstance(node,ast.Subscript):
  assert isinstance(node.value,ast.Name) and node.value.id in ['sequence','value','envelope'] and isinstance(node.slice,ast.Constant) and node.slice.value=='tstates'
  return ast.Subscript(copy.deepcopy(node.value),ast.Constant('m1_fetches'),ast.Load())
 if isinstance(node,ast.BinOp):
  if isinstance(node.op,ast.Mult):assert isinstance(node.left,ast.Constant);return ast.BinOp(copy.deepcopy(node.left),ast.Mult(),tone_fetch(node.right))
  return ast.BinOp(tone_fetch(node.left),copy.deepcopy(node.op),tone_fetch(node.right))
 if isinstance(node,ast.IfExp):return ast.IfExp(copy.deepcopy(node.test),tone_fetch(node.body),tone_fetch(node.orelse))
 return fetch(node)

class Tone(Emit):
 def visit_Name(self,node):
  if node.id in HELPERS:node.id=HELPERS[node.id]
  return node
 def visit_AugAssign(self,node):
  node=self.generic_visit(node)
  if isinstance(node.target,ast.Name) and node.target.id=='cost':return [node,ast.AugAssign(ast.Name('m1',ast.Store()),copy.deepcopy(node.op),tone_fetch(node.value))]
  return node

def main():
 source=(ROOT/'tools/audio_tone_channel_cost.py').read_bytes();assert hashlib.sha256(source).hexdigest()==AUDITED_SHA,'Reaudit tone instruction annotations'
 function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef));function=Tone().visit(function);function.name='tone_channel_refresh';ast.fix_missing_locations(function)
 header='"""Generated84C7 semantic state/cost/M1 composition;see generate_tone_channel_refresh.py."""\n'
 header+=f'# Cost-plan SHA256: {AUDITED_SHA}\nfrom audio_note_sequence_refresh import note_sequence_refresh\nfrom audio_pitch_refresh import pitch_refresh\nfrom audio_envelope_refresh import adsr_refresh,table_envelope_refresh\n\n'
 (ROOT/'tools/audio_tone_channel_refresh.py').write_text(header+ast.unparse(function)+'\n')
 print('84C7 M1 composition emitted from audited plan andverified semantic submodels.')
if __name__=='__main__':main()
