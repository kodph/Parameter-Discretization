import os
import socket
import time
import toml
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

    def __init__(self, executable_path=None, keep_alive=False, convert_results=True, log_level=0):
        super().__init__()

        # define aliases for standard methods
        self.simulate_testrun = self._evaluate_instance
        self.simulate_testruns = self._evaluate_instances
        self.simulate_movies = self._evaluate_movies
        self.simulate_movie = self._evaluate_movie

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
        executable_cmd = f'{self._executable_path} -cmdport {self._tcp_cmd_port} -apphost localhost' # use localhost
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

    # added for simulate movies.
    def _evaluate_movie(self, testrun_path, out_quants, camera_name='Dev_Xu', mode='save_all'):
        if not self._keep_alive: # assume that runner is shut down at this point, TODO: needs check to see if runner ist really shut down
            self.startup()
        _, testrun_basepath = testrun_path.split('TestRun\\')
        self.loadtestrun(testrun_path.replace('\\','\\\\')) #quick and dirty hack for the above problem
        self.savemode(mode)
        self.movie_start()
        for _ in range(1000000): # make sure the IPGmovie is running
            if self.movie_attach() == 1:
                break
        self.select_camera(camera_name)
        self.outquantsdelall()
        self.outquantsadd(out_quants)
        self.setresultfname('%o/%r/%D/%f_%T%?_s')# default is %t instead of %f. %t uses the whole source file path, with is unreadable
        self.startsim()

        self.waitforstatus_running(10000)
        self.waitforstatus_idle()
            # evaluate movie
        if not os.path.exists(f'{self.project_path}/png'):
            os.mkdir(f'{self.project_path}/png')
        movie_path = f'{self.project_path}/png/{testrun_basepath}.png'
        self.png_export(movie_path, 0, 'end', 'end')
            
            # evaluate result
        erg_path = self.getlastresultfname()
        erg_path = os.path.join(self.project_path,erg_path)
        if self._convert_results:
            erg = ERG(erg_path)
            simulation_result = {signal_name: signal.data for signal_name, signal in erg.signals.items()}

        if not self._keep_alive:
            if self._log_level <= 1:
                print('quit')
            self.application_shutdown()
            self.gui_quit()
        return movie_path, simulation_result
    
    def _evaluate_movies(self, grid_path, out_quants=['Vhcl.Fr1.x', 'Vhcl.Fr1.y','Vhcl.Fr1.z'], camera_name='Dev_Xu', mode='save_all'):
        with open(grid_path) as toml_file:
            grid = toml.load(toml_file)
            for key, value in grid['instances'].items():
                with open(value, 'r') as toml_file:
                    instance = toml.load(toml_file)
                with open(value, 'w') as toml_file:
                    try:
                        if instance['properties']['ipg_result'] == 0:
                            testrun_path = instance['properties']['path']
                            results = self._evaluate_movie(testrun_path, out_quants, camera_name, mode)
                            instance['results']['ipgmovie'] = results[0]
                            instance['results']['ipgresult'] = {key.replace('""',''): value[-1] for key,value in results[1].items()}
                            instance['properties']['ipg_result'] = 1
                        toml.dump(instance, toml_file)
                    except:
                        # Indicate which metadata is being modified when the program is interrupted
                        raise ValueError('this instance metadata ' + str(value) + ' is damaged') 
                    
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

    # added for send command for IPGmovie
    def movie_start(self):
        self._send_command(f'Movie start')

    def movie_loadsimdata(self, erg_file_path, options=None):
        self._send_command(f'Movie loadsimdata {erg_file_path} {options}')
    
    def png_export(self, movie_path, windowId, starttime, endtime):
        movie_path = movie_path.replace('\\', '\\\\')
        movie_path = movie_path.replace('/', '\\\\')
        movie_path = movie_path.replace("'","\"")
        self._send_command(f'Movie export window {movie_path} {windowId} -start {starttime} -end {endtime}')
    
    def movie_export(self, movie_path, windowId):
        movie_path = movie_path.replace('\\', '\\\\')
        movie_path = movie_path.replace('/', '\\\\')
        movie_path = movie_path.replace("'","\"")
        self._send_command(f'Movie export window {movie_path} {windowId}')

    def movie_attach(self):
        movie_attach = int(self._send_command(f'Movie attach'))
        return movie_attach

    def select_camera(self, camera_name):
        self._send_command(f'Movie camera select ' + camera_name)
    
 
# cm = CarMakerRunner()
# print(cm.projectinfo_path())
# a = r"C:\Users\user\Documents\1_Eigene_Projekte\90_Sonstiges\osc_param_variation\sample_data\Testruns\Autobahn Demo"
# b = r'..\\..\\..\\..\\Users\\user\\Documents\\1_Eigene_Projekte\\90_Sonstiges\\osc_param_variation\\sample_data\\Testruns\\Autobahn Demo'
# erg_path = cm.simulate_testrun(b, ['Time', 'Car.v'])
# print(erg_path)