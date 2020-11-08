import pickle
import os
import subprocess

os.chdir("Z:\\yard_pano\\4")
import glob
fnames = glob.glob("*.jpg")
print(fnames)
cmd = ["c:\\Program Files\\Hugin\\bin\\pto_gen.exe", "-o", "initial.pto"]
cmd.extend(fnames)
subprocess.call(cmd)
pto_vars=pickle.load(open("pto_vars.pkl", "rb"))
f = open("pto_vars", "w")
for i, fname in enumerate(fnames):
    roll, pitch, yaw = pto_vars[fname]
    f.write("r%d=%.3f,p%d=%.3f,y%d=%.3f\n" % (i, roll, i, -pitch, i, yaw))
f.close()
subprocess.call(["c:\\Program Files\\Hugin\\bin\\pto_var", "--set-from-file", "pto_vars", "initial.pto"])
#f = open("processed.pto", "w")
#f.write("".join(output_lines))

#subprocess.call(['C:\\Program Files\\Hugin\\bin\\cpfind.exe', '--prealigned', '-o', 'processed.cpfind.pto', 'processed.pto'])
