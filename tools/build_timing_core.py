"""Build a separate read-only timing GX DLL using the installed Windows GCC.
Use native subprocess argv; MSYS bash cannot create its signal pipe here.
"""
import argparse,os,shlex,subprocess
from pathlib import Path
from actor_reference import ROOT

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--target',default='genesis_plus_gx_timing_libretro.dll');args=parser.parse_args()
 workspace=ROOT.parents[1];cwd=workspace/'work/genesis-plus-gx';gcc='C:/msys64/ucrt64/bin/gcc.exe'
 env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
 command=[str(workspace/'work/sgdk/bin/make.exe'),'-n','-f','Makefile.libretro','platform=win',f'TARGET={args.target}',f'CC={gcc}','CXX=C:/msys64/ucrt64/bin/g++.exe','GIT_VERSION=','SHELL=C:/Windows/System32/cmd.exe']
 plan=subprocess.run(command,cwd=cwd,capture_output=True,text=True);assert plan.returncode==0,plan.stderr
 logs=[]
 for line in plan.stdout.splitlines():
  if not line.startswith(gcc):continue
  result=subprocess.run(shlex.split(line),cwd=cwd,capture_output=True,text=True,env=env)
  logs.append(line+'\n'+result.stdout+result.stderr);assert result.returncode==0,logs[-1]
 (ROOT/'validation/timing-core-build-python.log').write_text('\n'.join(logs))
 print(cwd/args.target)
if __name__=='__main__':main()
