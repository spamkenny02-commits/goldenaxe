"""Verify numbered ROM bytes in Git against immutable release SHA-256 values."""
import hashlib,json,subprocess
from actor_reference import ROOT

def main():
 rows=json.loads((ROOT/'versions/index.json').read_text())
 requests=['HEAD:versions/'+r['rom'] for r in rows]
 result=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=('\n'.join(requests)+'\n').encode(),capture_output=True,check=True)
 data=result.stdout;position=total=0
 for row in rows:
  end=data.index(b'\n',position);header=data[position:end].split()
  assert len(header)==3 and header[1]==b'blob',('ROM missing from Git',row['version'],header)
  size=int(header[2]);position=end+1
  blob=data[position:position+size];position+=size+1
  assert hashlib.sha256(blob).hexdigest()==row['sha256'],('Git ROM hash mismatch',row['version'])
  assert (ROOT/'versions'/row['rom']).read_bytes()==blob,('Local ROM differs',row['version'])
  total+=size
 assert position==len(data)
 print('Git ROM verification:',len(rows),'numbered ROMs match release SHA-256 and local bytes;',total,'bytes')

if __name__=='__main__':main()
