import os
import socket
import time
from .base import BaseRunner
from third_party.cmerg.erg import  ERG

class CarMakerCommandError(Exception):
    pass

class TclTransmissionError(Exception):
    pass

class CarMakerRunner(BaseRunner):
    SIMSTATUSES = {-1:'Preprocessing',
                -2:'Idle',
                -3:'Postprocessing',
                -4:'Model Check',
                -5:'Driver Adaption',
                -6:'FATAL ERROR / Emergency Mode',
                -7:'Waiting for License',
                -8:'Simulation paused',
                -10:'Starting application',
                -11:'Simulink initialization'}

    def __init__(self, project_path,executable_path=None, keep_alive=False, convert_results=True, log_level=0):
        super().__init__()

        # define aliases for standard methods
        self.simulate_testrun = self._evaluate_instance
        self.simulate_testruns = self._evaluate_instances

        if executable_path:
            self._executable_path = executable_path
        else:
            self._executable_path = r"C:\IPG\carmaker\win64-10.0\bin\CM.exe"
        self._tcp_cmd_port = 1024
        self._host = 'localhost'
        self._buffer = 4096
        self._RAISE_ON_TCL_ERROR = True
        self._keep_alive = keep_alive
        self._convert_results = convert_results
        self._log_level = log_level
        self._project_path = project_path
        if self._keep_alive:
            self.startup() # start runner at init, since it should never be shut down

    def _send_command(self, command):
        if self._log_level <= 0:
            print(f'TCL -> {command}')
        self._socket.send(bytes(f'{command}\n', 'utf-8'))
        reply = self._socket.recv(self._buffer)
        reply = reply.decode('utf-8').replace('\r\n','')
        tcl_error = reply[:1]
        if tcl_error == 'O':
            pass # received Ok
        elif tcl_error == '':
            pass # nothing received
        elif tcl_error == 'E':
            if self._RAISE_ON_TCL_ERROR:
                raise CarMakerCommandError(f'Unknown CarMaker Command:\n{command}')
        else:
            raise TclTransmissionError(f"Unknown TCL return code either 'E' or 'O' expected. \n Received: '{tcl_error}'")
        reply = reply[1:] # Strip E/O message
        if self._log_level <= 0:
            print(f'TCL <- {reply}')
        return reply

    def startup(self):
        executable_cmd = f'{self._executable_path} -cmdport {self._tcp_cmd_port}'
        if self._log_level <= 1:
            print(f'Executing: {executable_cmd}')
        os.system(executable_cmd)
        if self._log_level <= 1:
            print('Establishing TCP connection', end='')
        for _ in range(100):
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect((self._host, self._tcp_cmd_port))
                print('')
                break
            except:
                print('.',end='')
                time.sleep(0.1)
        self.project_path = self.projectinfo_path()
        if self._log_level <= 1:
            print(f'Project directory: {self.project_path}')
            print(f'CarMaker Ready')

    def _evaluate_instance(self, testrun_path, out_quants=[], mode='save_all'):
        if not self._keep_alive: # assume that runner is shut down at this point, TODO: needs check to see if runner ist really shut down
            self.startup()
        # self.loadtestrun(testrun_path) #TODO fix \\ -> \\\\ escape for paths
        self.loadtestrun(testrun_path.replace('\\','\\\\')) #quick and dirty hack for the above problem
        self.outquantsdelall()
        self.outquantsadd(out_quants)
        self.savemode(mode)
        self.setresultfname('%o/%r/%D/%f_%T%?_s')# default is %t instead of %f. %t uses the whole source file path, with is unreadable
        self.startsim()
        try:
            self.waitforstatus_running(10000)
            self.waitforstatus_idle()
            erg_path = self.getlastresultfname()
            erg_path = os.path.join(self.project_path,erg_path)
            if self._convert_results:
                erg = ERG(erg_path)
                simulation_result = {signal_name: signal.data for signal_name, signal in erg.signals.items()}
        except BaseException as E:
            simulation_result = None
        finally:
            if not self._keep_alive:
                if self._log_level <= 1:
                    print('quit')
                self.application_shutdown()
                self.gui_quit()
            return simulation_result

    def _evaluate_instances(self, testrun_paths, out_quants=[], mode='save_all'):
        erg_paths = {}
        for testrun_id, testrun_path in enumerate(testrun_paths):
            if self._log_level <= 1:
                print(f'Simulating Testrun {testrun_id}/{len(testrun_paths)}')
            erg_path = self._evaluate_instance(testrun_path, out_quants, mode)
            erg_paths[testrun_path] = erg_path
        return erg_paths

    def simulate_testrun_dir(self, testrun_dir_path, out_quants=[], mode='save_all'):
        dir_entries = os.listdir(testrun_dir_path)
        testrun_paths = [os.path.join(testrun_dir_path, entry) for entry in dir_entries]
        erg_paths = self.simulate_testruns(testrun_paths, out_quants, mode)
        return erg_paths
    
    def generate_results(self, testrun_dir_path, mode='save_all'):
        dir_entries = os.listdir(testrun_dir_path)
        testrun_paths = [os.path.join(testrun_dir_path, entry) for entry in dir_entries]
        erg_paths = []
        for testrun_path in testrun_paths:
            erg_path = self.generate_result(testrun_path, mode)
            erg_paths.append(erg_path)
        return erg_paths

    # added only for simulate results. And these results are appropriate for generate IPGmovies. 
    def generate_result(self, testrun_path, mode='save_all'):
        if not self._keep_alive: # assume that runner is shut down at this point, TODO: needs check to see if runner ist really shut down
            self.startup()
        
        ipgmovie_quants = ['Vhcl.Distance', 'Vhcl.Engine.rotv', 'Vhcl.FL.Fx', 'Vhcl.FL.Fy', 'Vhcl.FL.Fz', 'Vhcl.FL.LongSlip', 'Vhcl.FL.rot', 'Vhcl.FL.rotv', 'Vhcl.FL.rx', 'Vhcl.FL.ry', 'Vhcl.FL.rz', 'Vhcl.FL.SideSlip', 'Vhcl.FL.Trq_B2WC', 'Vhcl.FL.Trq_Brake', 'Vhcl.FL.Trq_DL2WC', 'Vhcl.FL.Trq_Drive', 'Vhcl.FL.Trq_T2W', 'Vhcl.FL.Trq_WhlBearing', 'Vhcl.FL.tx', 'Vhcl.FL.ty', 'Vhcl.FL.tz', 'Vhcl.FL.vBelt', 'Vhcl.FR.Fx', 'Vhcl.FR.Fy', 'Vhcl.FR.Fz', 'Vhcl.FR.LongSlip', 'Vhcl.FR.rot', 'Vhcl.FR.rotv', 'Vhcl.FR.rx', 'Vhcl.FR.ry', 'Vhcl.FR.rz', 'Vhcl.FR.SideSlip', 'Vhcl.FR.Trq_B2WC', 'Vhcl.FR.Trq_Brake', 'Vhcl.FR.Trq_DL2WC', 'Vhcl.FR.Trq_Drive', 'Vhcl.FR.Trq_T2W', 'Vhcl.FR.Trq_WhlBearing', 'Vhcl.FR.tx', 'Vhcl.FR.ty', 'Vhcl.FR.tz', 'Vhcl.FR.vBelt', 'Vhcl.Fr1.x', 'Vhcl.Fr1.y', 'Vhcl.Fr1.z', 'Vhcl.Fr1B.rx', 'Vhcl.Fr1B.ry', 'Vhcl.GearNo', 'Vhcl.Hitch.x', 'Vhcl.Hitch.y', 'Vhcl.Hitch.z', 'Vhcl.Ignition', 'Vhcl.OperationError', 'Vhcl.OperationState', 'Vhcl.Pitch', 'Vhcl.PitchAcc', 'Vhcl.PitchVel', 'Vhcl.PoI.ax', 'Vhcl.PoI.ax_1', 'Vhcl.PoI.ay', 'Vhcl.PoI.ay_1', 'Vhcl.PoI.az', 'Vhcl.PoI.az_1', 'Vhcl.PoI.GCS.Elev', 'Vhcl.PoI.GCS.Lat', 'Vhcl.PoI.GCS.Long', 'Vhcl.PoI.vx', 'Vhcl.PoI.vx_1', 'Vhcl.PoI.vy', 'Vhcl.PoI.vy_1', 'Vhcl.PoI.vz', 'Vhcl.PoI.vz_1', 'Vhcl.PoI.x', 'Vhcl.PoI.y', 'Vhcl.PoI.z', 'Vhcl.RL.Fx', 'Vhcl.RL.FxTwin', 'Vhcl.RL.Fy', 'Vhcl.RL.FyTwin', 'Vhcl.RL.Fz', 'Vhcl.RL.FzTwin', 'Vhcl.RL.LongSlip', 'Vhcl.RL.rot', 'Vhcl.RL.rotv', 'Vhcl.RL.rx', 'Vhcl.RL.ry', 'Vhcl.RL.rz', 'Vhcl.RL.SideSlip', 'Vhcl.RL.Trq_B2WC', 'Vhcl.RL.Trq_Brake', 'Vhcl.RL.Trq_DL2WC', 'Vhcl.RL.Trq_Drive', 'Vhcl.RL.Trq_T2W', 'Vhcl.RL.Trq_WhlBearing', 'Vhcl.RL.tx', 'Vhcl.RL.ty', 'Vhcl.RL.tz', 'Vhcl.RL.vBelt', 'Vhcl.Road.JuncObjId', 'Vhcl.Road.LinkObjId', 'Vhcl.Road.nextJuncObjId', 'Vhcl.Road.onJunction', 'Vhcl.Road.s2lastJunc', 'Vhcl.Road.s2nextJunc', 'Vhcl.Roll', 'Vhcl.RollAcc', 'Vhcl.RollVel', 'Vhcl.RR.Fx', 'Vhcl.RR.FxTwin', 'Vhcl.RR.Fy', 'Vhcl.RR.FyTwin', 'Vhcl.RR.Fz', 'Vhcl.RR.FzTwin', 'Vhcl.RR.LongSlip', 'Vhcl.RR.rot', 'Vhcl.RR.rotv', 'Vhcl.RR.rx', 'Vhcl.RR.ry', 'Vhcl.RR.rz', 'Vhcl.RR.SideSlip', 'Vhcl.RR.Trq_B2WC', 'Vhcl.RR.Trq_Brake', 'Vhcl.RR.Trq_DL2WC', 'Vhcl.RR.Trq_Drive', 'Vhcl.RR.Trq_T2W', 'Vhcl.RR.Trq_WhlBearing', 'Vhcl.RR.tx', 'Vhcl.RR.ty', 'Vhcl.RR.tz', 'Vhcl.RR.vBelt', 'Vhcl.sRoad', 'Vhcl.Steer.Acc', 'Vhcl.Steer.Ang', 'Vhcl.Steer.Trq', 'Vhcl.Steer.Vel', 'Vhcl.tRoad', 'Vhcl.v', 'Vhcl.Wind.vx', 'Vhcl.Wind.vy', 'Vhcl.Wind.vz', 'Vhcl.Yaw', 'Vhcl.YawAcc', 'Vhcl.YawRate']
        _, testrun_path = testrun_path.split('TestRun\\')
        self.loadtestrun(testrun_path.replace('\\','\\\\')) #quick and dirty hack for the above problem
        self.outquantsadd(ipgmovie_quants)
        self.savemode(mode)
        #self.setresultfname('%o/%r/%D/%f_%T%?_s')# default is %t instead of %f. %t uses the whole source file path, with is unreadable
        self.startsim()
        try:
            self.waitforstatus_running(10000)
            self.waitforstatus_idle()
            erg_path = self.getlastresultfname()
            erg_path = os.path.join(self.project_path, erg_path)
            #if self._convert_results:
                #erg = ERG(erg_path)
                #simulation_result = {signal_name: signal.data for signal_name, signal in erg.signals.items()}
        except BaseException as E:
            simulation_result = None
        finally:
            if not self._keep_alive:
                if self._log_level <= 1:
                    print('quit')
                self.application_shutdown()
                self.gui_quit()
            return erg_path
    
    def generate_movies(self, testrun_dir_path, mode='save_all'):
        erg_paths = self.generate_results(testrun_dir_path, mode)
        testrun_dir_path = testrun_dir_path.split('\\')
        dir_path = testrun_dir_path[-1] # Get the folder name of the test instances
        if not self._keep_alive: # assume that runner is shut down at this point, TODO: needs check to see if runner ist really shut down
            self.startup()
        self.movie_start()
        for i, erg_path in enumerate(erg_paths):
            erg_path = erg_path.replace('/','\\\\')
            erg_path = erg_path.replace('\\','\\\\')
            self.movie_loadsimdata(erg_path)
            if not os.path.exists(f'{self._project_path}/png'):
                os.mkdir(f'{self._project_path}/png')
            if not os.path.exists(f'{self._project_path}/png/{dir_path}'):
                os.mkdir(f'{self._project_path}/png/{dir_path}')
            self.movie_export(f'{self._project_path}/png/{dir_path}/test{i:02}.png', 0, 0.05, 0.05)
            if self._log_level <= 1:
                print(f'png{i:02} saved')
        self.gui_quit()
        pass    
   
    def startsim(self):
        self._send_command(f'StartSim')

    def stopsim(self):
        self._send_command(f'StopSim')

    def simstatus(self):
        sim_status = int(self._send_command(f'SimStatus'))
        if sim_status not in self.SIM_STATES:
            return sim_status
        else:
            return sim_status, self.SIM_STATES[sim_status]

    def waitforstatus(self, status, timeout=''):
        sim_status = self._send_command(f'WaitForStatus {status} {timeout}')
        if int(sim_status) != 0:
            raise TimeoutError(f'waitforstatus timed out after {timeout} ms')

    def waitforstatus_running(self, timeout=''):
        sim_status = self.waitforstatus('running', timeout)

    def waitforstatus_idle(self, timeout=''):
        sim_status = self.waitforstatus('idle', timeout)

    def loadtestrun(self, path):
        self._send_command(f'LoadTestRun "{path}"')

    def quantsubscribe(self, quantities):
        self._send_command(f'QuantSubscribe {{{" ".join(quantities)}}}')

    def outquantsadd(self, quantities):
        self._send_command(f'OutQuantsAdd {{{" ".join(quantities)}}}')

    def outquantsdel(self, quantities):
        self._send_command(f'OutQuantsDel {{{" ".join(quantities)}}}')

    def outquantsdelall(self):
        self._send_command(f'OutQuantsDelAll')

    def savemode(self, mode='save_all'):
        self._send_command(f'SaveMode {mode}')

    def getlastresultfname(self):
        return self._send_command(f'GetLastResultFName')

    def setresultfname(self, fname):
        return self._send_command(f'SetResultFName {fname}')

    def projectinfo_path(self):
        return self._send_command(f'ProjectInfo path')

    def projectinfo_version(self):
        return self._send_command(f'ProjectInfo version')

    def application_shutdown(self):
        self._send_command(f'Application shutdown')

    def application_appinfo(self):
        self._send_command(f'Application appinfo')

    def application_cmversion(self):
        self._send_command(f'Application cmversion')

    def gui_quit(self):
        self._send_command(f'GUI quit')

    def gui_version(self):
        self._send_command(f'GUI version')

    def popupctrl_timeout(self, timeout='-1'):
        self._send_command(f'PopupCtrl timeout {timeout}')

# added for send command movie
    def movie_start(self):
        self._send_command(f'Movie start')

    def movie_loadsimdata(self, erg_file_path, options=None):
        self._send_command(f'Movie loadsimdata {erg_file_path} {options}')
    
    def movie_export(self, movie_path, windowId, starttime, endtime):
        movie_path = movie_path.replace('\\', '\\\\')
        movie_path = movie_path.replace('/', '\\\\')
        movie_path = movie_path.replace("'","\"")
        self._send_command(f'Movie export window {movie_path} {windowId} -start {starttime} -end {endtime}')
    
    def movie_attach(self):
        self._send_command(f'Movie attach')

 
# cm = CarMakerRunner()
# print(cm.projectinfo_path())
# a = r"C:\Users\user\Documents\1_Eigene_Projekte\90_Sonstiges\osc_param_variation\sample_data\Testruns\Autobahn Demo"
# b = r'..\\..\\..\\..\\Users\\user\\Documents\\1_Eigene_Projekte\\90_Sonstiges\\osc_param_variation\\sample_data\\Testruns\\Autobahn Demo'
# erg_path = cm.simulate_testrun(b, ['Time', 'Car.v'])
# print(erg_path)