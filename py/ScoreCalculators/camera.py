import math
import numpy as np

def transform_matrix_carmera(camera_name, camera_cfg_filpath = r"C:\Arbeit\Carmaker_test\Movie\Camera.cfg"):
    breakinfo = 0
    with open(camera_cfg_filpath) as camera_txt:
        for line in camera_txt:
            if breakinfo == 0:
                if '=' in line:
                    check_camera_name = line.split('=')[1].strip()
                    if check_camera_name == camera_name:
                        breakinfo = 1
            else:
                if '=' in line:
                    check_letter = line.split('=')[0].split('.')[2].strip()
                    if check_letter == 'Pos':
                        pos = line.split('=')[1].strip().split(' ')
                        pos = [float(pos[0]), float(pos[1]), float(pos[2])]
                    if check_letter == 'dist':
                        dist = line.split('=')[1].strip()
                        dist = float(dist)
                    if check_letter == 'rot':
                        rot = line.split('=')[1].strip().split(' ')
                        rot = [float(rot[0]), float(rot[1]), float(rot[2])]
                        break
        R = Rotation(rot)
        T = [-(dist-pos[0]), pos[1], pos[2]]
        human36m_camera_intrinsic = {'R':R, 'T':T}
    return human36m_camera_intrinsic

def Rotation(rot):
    r = rot[0] 
    p = rot[1]
    y = rot[2]
    
    y = y*np.pi/180.0
    p = p*np.pi/180.0
    r = r*np.pi/180.0        
    
    Rr = np.matrix([[1.0, 0.0, 0.0],[0.0, np.cos(r), -np.sin(r)],[0.0, np.sin(r), np.cos(r)]])
    Rp = np.matrix([[np.cos(p), 0.0, np.sin(p)],[0.0, 1.0, 0.0],[-np.sin(p), 0.0, np.cos(p)]])
    Ry = np.matrix([[np.cos(y), -np.sin(y), 0.0],[np.sin(y), np.cos(y), 0.0],[0.0, 0.0, 1.0]])
    return Ry*Rp*Rr

def ground_truth(joint_world, human36m_camera_intrinsic, camera_name):
    camera_intrinsic = human36m_camera_intrinsic
    joint_world = np.asarray(joint_world)
    R = np.asarray(camera_intrinsic["R"])
    T = np.asarray(camera_intrinsic["T"])
    joint_cam = np.dot(R, (joint_world - T).T).T
    return joint_cam

def fov_f(fov, monitor_size=15.6, monitor_resolution=(1920, 1080), scale=1.25, png_resolution=(768, 576)):
    inch_m = 2.54/100
    ppi = math.sqrt(monitor_resolution[0]**2 + monitor_resolution[1]**2)/monitor_size
    ipp = 1/ppi
    if png_resolution[0] >= png_resolution[1]: 
        f = png_resolution[0]*ipp*inch_m*scale/(2*math.tan((fov/2)/180*math.pi))
    else:
        f = png_resolution[1]*ipp*inch_m*scale/(2*math.tan((fov/2)/180*math.pi))
    return f

def camera_pic(f, point):
    coor_x = ((f*point[1]/point[0])+0.1726/2)/0.1726
    coor_y = (0.1293/2-f*point[2]/point[0])/0.1293
    return (coor_x, coor_y)

def camera(joint_world, camera_name, fov=50):
    human36m_camera_intrinsic = transform_matrix_carmera(camera_name, camera_cfg_filpath = r"C:\Arbeit\Carmaker_test\Movie\Camera.cfg")
    joint_cam = ground_truth(joint_world, human36m_camera_intrinsic, camera_name)
    f = fov_f(fov)
    return (camera_pic(f,joint_cam))