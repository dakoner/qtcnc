import pickle
import os
import subprocess
import numpy
import glob

os.chdir("z:\\yard_pano\\12")
fnames = glob.glob("*.jpg")
pto_vars=pickle.load(open("pto_vars.pkl", "rb"))


cmd = ["c:\\Program Files\\Hugin\\bin\\pto_gen.exe", "-o", "initial.pto"]
cmd.extend(fnames)
subprocess.call(cmd)


print(pto_vars)
f = open("pto_vars", "w")

orientations = numpy.array(list(pto_vars.values()))
_, min_pitch, min_yaw = numpy.amin(orientations, axis=0)
_, max_pitch, max_yaw = numpy.amax(orientations, axis=0)

yaw_range = (max_yaw - min_yaw)
print(min_yaw, max_yaw, yaw_range)
pitch_range = (max_pitch - min_pitch)
print(min_pitch, max_pitch, pitch_range)

#print("mid_yaw:", mid_yaw)
for i, fname in enumerate(fnames):
    roll, pitch, yaw = pto_vars[fname]
    # centers yaw at 0
    print("From yaw", yaw, "to", yaw-min_yaw-(yaw_range/2))
    # puts highest value of pitch at 0
    #print("From pitch", pitch, "to", pitch-min_pitch-(pitch_range/2))

    f.write("r%d=%.3f,p%d=%.3f,y%d=%.3f\n" % (i, roll, i, 90-pitch, i, yaw-min_yaw-(yaw_range/2)))
f.close()
subprocess.call(["c:\\Program Files\\Hugin\\bin\\pto_var", "--set-from-file", "pto_vars", "-o", "initial_vars.pto", "initial.pto"])

#subprocess.call(['C:\\Program Files\\Hugin\\bin\\cpfind.exe',  '--prealigned', '-o', 'initial_vars_cpfind.pto', 'initial_vars.pto'])
