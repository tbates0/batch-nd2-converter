# -*- coding: utf-8 -*-
"""
Last Updated: 4/26/2017
@author: Tim Bates
Fujimori lab
University of California San Francisco
"""

from PyQt5 import QtCore, QtWidgets
from multiprocessing import Pool, current_process
from time import ctime, time
import os, subprocess, traceback, sys, json


def convert_file(cmd):
    """
    convert_file simply takes the string provided and executes in a command
    prompt in the specified working directory.
    Construction of cmd list:
    0 - full length command to be run by bfconvert.bat
    1 - name of file to be converted
    2 - name of file to be created
    3 - location of bfconvert.bat
    4 - output folder path
    If you create a method to convert files in script then simply replace this
    function with your code and no other aspects of the GUI or file handling
    will need be changed significantly.
    """    
    try:     
        os.chdir(cmd[3])
        pipe = subprocess.Popen(cmd[0], stdin=subprocess.PIPE, \
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        stdout, stderr = pipe.communicate()
        if "'bfconvert' is not recognized" in str(stdout):
            return ('Error: bftools could not be located',cmd)
        if os.path.isfile(os.path.join(cmd[4],cmd[2])):
            if os.stat(os.path.join(cmd[4],cmd[2])).st_size != 0:
                return cmd[2][len(cmd[4])+1:] + ' created at ' + \
                ctime()[11:19] + ' by ' + str(current_process())[19:31]
            else:
                return ['Error: 0 size file created',cmd]
        else:
            return ['Error: no file created',cmd]
    except Exception as z:
        return ['Error: python exception during conversion',z,cmd]

def converter(self,params):
    """
    The converter function takes the parameters specified by the user in the
    GUI, finds all of the convertible nd2 files, assembles a list of commands
    to pass to the worker processes, and logs each action. UserWarning found
    anywhere in this function writes the error to log and returns to the GUI
    for the user to try to correct the issue.
    """
    try:
#Unpack variables from GUI (User Input Class) specifying run arguments
        folder = params[0]
        outfolder = params[1]
        series = params[2]
        channel = params[3]
        zseries = params[4]
        timepoint = params[5]
        ID = params[6]
        notes = params[7]
        ftype = params[8]
        bfcp = params[9] #location of bftools (bfconvert)

#sets start time for operations and creates ID number to identify runs
        time1 = ctime()
        time2 = time()
#This only happens if somehow the user does not set an ID in the GUI
        if ID == '':
            ID = time1[4:7] + time1[8:10] + time1[-4:] + time1[11:13] + \
            time1[14:16] + time1[17:19]
            
#make log file, place in output folder
        logname = 'log.' + ID + '.txt'
        print(logname)
        f = open(os.path.join(outfolder,logname),'a+')

#check for path formatting errors depending on method of entry   
        if folder == '':
            print('No folder chosen to convert')
        elif folder[0] == 'r':
            folder = folder[2:-1]
        elif folder[0] == '"':
            folder = folder[1:-1]
           
#log settings for this run
        print('working directory: ' + folder + '\n')
        f.write('input path: ' + folder + '\n')
        f.write('output path: ' + outfolder + '\n')
        f.write('bfconvert path: ' + bfcp + '\n')
        f.write('series = ' + str(series) + '\n')
        f.write('channels = ' + str(channel) + '\n')
        f.write('z planes = ' + str(zseries) + '\n')
        f.write('timepoints = ' + str(timepoint) + '\n')
        f.write('ID number for this run = ' + str(ID) + '\n')
        f.write('Convert to file type: ' + ftype + '\n')
        f.write('User Notes: \n' + notes + '\n\n')
        f.flush()
        
#check again that input and output folders exist
        checkthese = [folder,outfolder]
        for i in checkthese:
            if os.path.isdir(i) != True:
                raise UserWarning('Folder Does Not Exist: ' + i)
        if os.path.isfile(os.path.join(bfcp,'bfconvert.bat')) != True:
            raise UserWarning('bftools Not Found At Given Location')
        print('all folders located')

#Creates list of all nd2 files in entered directory        
        nd2s = []
        print('Found Files:')
        f.write('Found Files:' + '\n')
        for filename in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, filename)):
                if filename[-4:] == '.nd2':        
                    print(filename)
                    f.write(filename + '\n')
                    nd2s.append(filename)
                else:
                    print(filename + ' ***is not an nd2 file and will not be \
converted')
                    f.write(filename + ' ***is not an nd2 file and will not be\
 converted\n')
        f.flush()

#Creates a list of commands to pass to the converter processes
#The commands are designed to be entered in a windows command prompt
        commands = []
        for image in nd2s:
            for i in range(timepoint):
                for j in range(zseries):
                    for k in range(series):
                        for l in range(channel):
                            infile = '"' + folder + '\\' + image + '"'
                            outfile = '"' \
                            + outfolder + '\\' \
                            + ID + '_' + image[13:17] \
                            + 't' + str(i)\
                            + '_z' + str(j)\
                            + '_s' + str(k)\
                            + '_c' + str(l)\
                            + ftype + '"'
                            cmd = \
                            'bfconvert -overwrite -no-upgrade'\
                            + ' -timepoint ' + str(i)\
                            + ' -z ' + str(j)\
                            + ' -series ' + str(k)\
                            + ' -channel ' + str(l)\
                            + ' ' + infile + ' ' + outfile
                            commands.append(\
                            [cmd,infile[1:-1],outfile[1:-1],bfcp,outfolder])
                            

#returns to GUI if no nd2 files are found
        if len(nd2s) == 0:
            print('No nd2 files found at input location')
            f.write('No nd2 files found at input location')
            raise UserWarning('No convertible files located, returning to GUI')

#asks user's permission to start potentially lengthy conversion process
#I can't think of a good way to estimate time of process without data from
#previous runs, which I do not save.       
        cont = conf(self, str(len(nd2s)), str(len(commands)))
        if cont == False:
            raise UserWarning('User Aborted Conversion, Returning to GUI.')
        else:
            f.write('User Accepted Conversion List')

        print('Total Files Found: '+ str(len(nd2s)))
        f.write('Total Files Found: '+ str(len(nd2s))+ '\n')
        print('Conversion Started at: '+ ctime())
        f.write('Conversion Started at: '+ ctime() + '\n')
        f.flush()

#creates workers for multiprocessing and sends info to the conversion function
#each worker takes 1 nd2 file at a time and converts it to tiff files
#everything in the for loop is for error checking and progress bar stuff
        retry = []
        completed = 0
        total = len(commands)
        errors = 0
        p = Pool()
        for x in p.imap_unordered(convert_file,commands):
            if type(x) == str:
                completed += 1
                curtime = time()
                sofar = curtime - time2
                timeleft = (sofar / completed) * (total - completed)
                if timeleft > 60:
                    timeleft = timeleft // 60
                    timeleft = str(round(timeleft)) + ' Minutes'
                else:
                    timeleft = str(round(timeleft)) + ' Seconds'
                if sofar > 60:
                    sofar = sofar // 60
                    sofar = str(round(sofar)) + ' Minutes'
                else:
                    sofar = str(round(sofar)) + ' Seconds'
                QtCore.QCoreApplication.processEvents()
                self.pbar.setValue(float(completed)/float(total)*1000)
                self.output.setText('{0} of {1} : {2}\nElapsed Time: {3}\n\
Estimated Time Remaining: {4}'.format(str(completed),str(total),\
                x,sofar,timeleft))
                print(str(completed)+ ' of '+ str(total)+ ': '+ x)
                f.write(str(completed) + ' of '+ str(total) + ': ' + x + '\n')
            elif type(x) == list:
                print('{0}:\n{1} for {2}'.format(x[0],str(x[1]),x[2][1]))
                f.write('{0}:\n{1} for {2}\n'.format(x[0],str(x[1]),x[2][1]))
                errors += 1
            elif type(x) == tuple:
                print(x[0])
                f.write(x[0])
                raise UserWarning('bftools could not be located, \
please double check the location of the bftools folder.')
        f.flush()
                
#Error correction step retrys conversion of frames with non-fatal errors
#this error is usually creation of a 0 size file, which I check for explicitly
#in the converter function
        print('Conversion attempted for all files, beginning error check')
        f.write('Conversion attempted for all files, beginning error check\n')
        if retry != []:
            print(str(len(retry)) + \
            ' files were not properly converted, retrying now')
            f.write(str(len(retry)) + \
            ' files were not properly converted, retrying now\n')
        else:
            print('No errors were found')
            f.write('No errors were found\n')
        for item in retry:
            x = convert_file(item[1])
            if type(x) == str:
                print(x)
                f.write(x)
                errors -= 1
                completed += 1
                curtime = time()
                sofar = curtime - time2
                timeleft = (sofar / completed) * (total - completed)
                if timeleft > 60:
                    timeleft = timeleft // 60
                    timeleft = str(round(timeleft)) + ' Minutes'
                else:
                    timeleft = str(round(timeleft)) + ' Seconds'
                if sofar > 60:
                    sofar = sofar // 60
                    sofar = str(round(sofar)) + ' Minutes'
                else:
                    sofar = str(round(sofar)) + ' Seconds'
                QtCore.QCoreApplication.processEvents()
                self.pbar.setValue(float(completed)/float(total)*1000)
                self.output.setText('{0} of {1} : {2}\nElapsed Time: {3}\n\
Estimated Time Remaining: {4}'.format(str(completed),str(total),\
                x,sofar,timeleft))
            else:
                print('Could not fix error, please check settings')
                f.write('Could not fix error, please check settings\n')
        f.flush()
#if no errors exist after finishing correction step then tells user the run
#is finished and prompts them to exit. Otherwise, notifies user of errors.
        if errors == 0:
            self.output.setText(str(total - errors) + ' of ' + str(total) +\
            ' Tiff Files Sucessfully Created\nClick Exit to leave the program')
            self.cancel.setText('Exit')
        else:
            self.output.setText(str(total - errors) + ' of ' + str(total) +\
            ' Tiff Files Sucessfully Created\nCheck log file for errors'\
            + '\nClick Exit to leave the program')
            self.cancel.setText('Exit')

#reports statistics for this run and returns to GUI for user to quit
        time3 = time()
        elapsed = time3 - time2
        print('Finished at ' + ctime())
        f.write('Finished at ' + ctime() + '\n')
        print('This job took ' + str(int(elapsed)) + ' seconds')
        f.write('This job took ' + str(int(elapsed)) + ' seconds\n')
        print('Time per frame ' + str(elapsed/completed)[:6] + 'seconds')
        f.write('Time per frame ' + str(elapsed/completed)[:6] + 'seconds\n')
        f.close()
        
#Exception handling section
#system exit is requested when the x is pressed
    except SystemExit as e:
        f.flush()
        print('System Exit requested')
        f.write('System Exit requested')
        f.close()
        sys.exit(e)
#User warnings are for handling of common internal errors such as no nd2 files
#found or unable to find bfconvert.  This returns to the GUI for the user to
#potentially correct the error and re-start.
    except UserWarning as err:
        try:
            p.terminate
        except:
            pass
        print(err)
        f.write(str(err))
        self.output.setText(str(err))
        self.run.setEnabled(True)
        f.close()
#Catches all other exceptions and prints to log file
#Seeing an error in this section is going to require some debugging
#Try to reproduce the error and look at the terminal, not the log file
#I havent been able to figure out how to print the entire traceback to file
    except Exception as z:
        try:
            p.terminate()
        except:
            pass
        print(traceback.print_exc())
        f.write('An Exception Occured:\n{0}'.format(z))
        self.output.setText('An Unknown Exception Occured\nFind someone that\
 knows python and bribe them with beer')
        f.close()
        
def conf(self, nd2, tiff):
    """ This is the confirmation dialog that tells the user how many files were
    found, how many files will be created, and asks if they want to continue.
    """
    msg = 'Found {0} nd2 files and will make {1} tiff files'.format(nd2,tiff)
    choice = QtWidgets.QMessageBox.question(self, 'Continue?',
                                        msg,
                                        QtWidgets.QMessageBox.Yes | \
                                        QtWidgets.QMessageBox.No)
    if choice == QtWidgets.QMessageBox.Yes:
        return True
    else:
        return False
        

class UserInput(QtWidgets.QWidget):
    """This class defines the User Interface which will collect the necessary
    parameters to run the converter program.  It was originally written in 
    PyQt4, but later converted to PyQt5.
    """
    
    def __init__(self):
        super(UserInput, self).__init__()
        
        self.initUI()
        
    def initUI(self):       
        
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        
        self.folder = QtWidgets.QPushButton('Folder to Convert')
        self.folderEdit = QtWidgets.QLabel()
        grid.addWidget(self.folder, 2, 0)
        grid.addWidget(self.folderEdit, 2, 1, 1, 4)
        self.folder.clicked.connect(self.get_folder)
        
        self.outfolder = QtWidgets.QPushButton('Output Folder')
        self.outfolderEdit = QtWidgets.QLabel()
        grid.addWidget(self.outfolder, 3, 0)
        grid.addWidget(self.outfolderEdit, 3, 1, 1, 4)
        self.outfolder.clicked.connect(self.get_outfolder)
        
        self.bffolder = QtWidgets.QPushButton('Location of bftools')
        self.bffolderEdit = QtWidgets.QLabel()
        grid.addWidget(self.bffolder, 4, 0)
        grid.addWidget(self.bffolderEdit, 4, 1, 1, 4)
        self.bffolder.clicked.connect(self.get_bffolder)
        
        self.series = QtWidgets.QPushButton('Series')
        self.seriesEdit = QtWidgets.QLabel('1')
        grid.addWidget(self.series, 6, 0)
        grid.addWidget(self.seriesEdit, 6, 1)
        self.series.clicked.connect(self.get_series)
        
        self.channel = QtWidgets.QPushButton('Channels')
        self.channelEdit = QtWidgets.QLabel('1')
        grid.addWidget(self.channel, 7, 0)
        grid.addWidget(self.channelEdit, 7, 1)
        self.channel.clicked.connect(self.get_channel)
        
        self.zseries = QtWidgets.QPushButton('Z-Series')
        self.zseriesEdit = QtWidgets.QLabel('1')
        grid.addWidget(self.zseries, 6, 2)
        grid.addWidget(self.zseriesEdit, 6, 3)
        self.zseries.clicked.connect(self.get_zseries)
        
        self.timepoint = QtWidgets.QPushButton('Timepoints')
        self.timepointEdit = QtWidgets.QLabel('1')
        grid.addWidget(self.timepoint, 7, 2)
        grid.addWidget(self.timepointEdit, 7, 3)
        self.timepoint.clicked.connect(self.get_timepoint)
        
        self.name = QtWidgets.QPushButton('Run Name')
        self.nameEdit = QtWidgets.QLabel()
        grid.addWidget(self.name, 11,0)
        grid.addWidget(self.nameEdit, 11,1)
        self.name.clicked.connect(self.get_name)
        
        usernotesnote = QtWidgets.QLabel('Place any notes below. These will be \
Included in the log file placed in the output folder.')        
        grid.addWidget(usernotesnote, 13,0,1,4)
        self.usernotes = QtWidgets.QLineEdit()
        grid.addWidget(self.usernotes, 14,0,1,4)
        
        self.default = QtWidgets.QPushButton('Set These As Default')
        self.resetdefault = QtWidgets.QPushButton('Reset Defaults File')
        self.restoredefault = QtWidgets.QPushButton('Restore Defaults')
        grid.addWidget(self.default, 16, 0)
        grid.addWidget(self.resetdefault, 16, 2)
        grid.addWidget(self.restoredefault, 16, 1)
        self.default.clicked.connect(self.save_defaults)
        self.resetdefault.clicked.connect(self.make_defaults)
        self.restoredefault.clicked.connect(self.set_defaults)
        
        self.help = QtWidgets.QPushButton('Help and Credits')
        grid.addWidget(self.help, 16, 3)
        #self.help.clicked.connect(self.help_window)
        self.help.clicked.connect(self.open_help)
        
        self.ftype = QtWidgets.QPushButton('Select Output Type')
        self.ftypeEdit = QtWidgets.QLabel('.tiff')
        self.ftypeNote = QtWidgets.QLabel\
        (': .tiff Recommended Due to Lossless Format')
        grid.addWidget(self.ftype, 12, 0)
        grid.addWidget(self.ftypeEdit, 12, 1)
        grid.addWidget(self.ftypeNote, 12, 2, 1, 2)
        self.ftype.clicked.connect(self.set_type)
        
        self.run = QtWidgets.QPushButton('Start Conversion')
        grid.addWidget(self.run, 17, 0)
        self.run.clicked.connect(self.start_convert)     
        
        self.cancel = QtWidgets.QPushButton('Cancel')
        grid.addWidget(self.cancel, 17, 3)
        self.cancel.clicked.connect(quit)        
        
        self.pbar = QtWidgets.QProgressBar(self)
        grid.addWidget(self.pbar, 17,1,1,2)
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(1000)
        
        self.output = QtWidgets.QLabel()
        grid.addWidget(self.output, 18,0,1,5)
        
        self.set_defaults()
        
        self.setLayout(grid)
        self.setWindowTitle('Batch Convert nd2 Files')    
        self.show()


    def set_defaults(self):
        """Checks for presence of save file (.json) and loads it, or creates it
        in order to set the default values for all parameters
        """
        if os.path.isfile('defaults.json') == True:
            defaultsfile = open('defaults.json','r')
            defaults = json.load(defaultsfile)
            self.folderEdit.setText(defaults['folder'])
            self.outfolderEdit.setText(defaults['outfolder'])
            self.bffolderEdit.setText(defaults['bffolder'])
            self.seriesEdit.setText(defaults['series'])
            self.channelEdit.setText(defaults['channel'])
            self.zseriesEdit.setText(defaults['zseries'])
            self.timepointEdit.setText(defaults['timepoint'])
            defaultsfile.close()
        else:
            self.make_defaults()
        time1 = ctime()
        ID = time1[4:7] + time1[8:10] + time1[-4:] + time1[11:13] + \
        time1[14:16] + time1[17:19]
        self.nameEdit.setText(ID)
    
    def make_defaults(self):
        """Makes a new defaults.json file with the default values listed below.
        This process will overwrite any existing save file, and will update all
        fields in the GUI with the reset values.
        """
        defaultsfile = open('defaults.json','w')
        defaults = {
        'folder': '',
        'outfolder': '',
        'bffolder' : os.getcwd(),
        'series': '1',
        'channel': '1',
        'zseries': '1',
        'timepoint': '1',
        }
        json.dump(defaults,defaultsfile)
        defaultsfile.close()
        self.folderEdit.setText(defaults['folder'])
        self.outfolderEdit.setText(defaults['outfolder'])
        self.bffolderEdit.setText(defaults['bffolder'])
        self.seriesEdit.setText(defaults['series'])
        self.channelEdit.setText(defaults['channel'])
        self.zseriesEdit.setText(defaults['zseries'])
        self.timepointEdit.setText(defaults['timepoint'])
        
    def save_defaults(self):
        """Simply saves values from all user editable fields as defaults.
        This process will overwrite any existing save file.  The notes section
        is not saved nor is the run name section.
        """
        defaultsfile = open('defaults.json','w+')
        defaults = {}            
        defaults['folder'] = str(self.folderEdit.text())
        defaults['outfolder'] = str(self.outfolderEdit.text())
        defaults['bffolder'] = str(self.bffolderEdit.text())
        defaults['series'] = str(self.seriesEdit.text())
        defaults['channel'] = str(self.channelEdit.text())
        defaults['zseries'] = str(self.zseriesEdit.text())
        defaults['timepoint'] = str(self.timepointEdit.text())
        json.dump(defaults,defaultsfile)

    def set_type(self):
        """Allows user to select from all currently available output formats
        of bfconvert in decending order of how much I like them subjectively.
        """
        options =['.tiff','.tif','.ome.tiff','.png','.jpg','.jp2','.ome',
        '.ome.xml','.avi','.mov','.ics','.ids','.ch5','.eps','.epsi','.ps',
        '.wlz']
        text,ok = QtWidgets.QInputDialog.getItem(self,\
        'Select a File Type','abc',options,editable=False)
        self.ftypeEdit.setText(text)
        
    def get_folder(self):
        """The following 8 functions open a dialog to set the value for the
        appropriate section in the GUI.
        """
        text = QtWidgets.QFileDialog.getExistingDirectory(self,\
        'Open Folder Containing .nd2 files')
        if text != '':
            self.folderEdit.setText(str(text))
        
    def get_outfolder(self):
        text = QtWidgets.QFileDialog.getExistingDirectory(self,\
        'Open Output Folder')        
        if text != '':
            self.outfolderEdit.setText(str(text))
        
    def get_bffolder(self):
        text = QtWidgets.QFileDialog.getExistingDirectory(self,\
        'Locate bftools Folder')
        if text != '':
            self.bffolderEdit.setText(str(text))
        
    def get_series(self):
        num,ok = QtWidgets.QInputDialog.getInt(self,\
        "Number of Series","enter a number",value=1,min=1)
        if str(num) != '':
            self.seriesEdit.setText(str(num))
        
    def get_channel(self):
        num,ok = QtWidgets.QInputDialog.getInt(self,\
        "Number of Channels","enter a number",value=1,min=1)
        if str(num) != '':
            self.channelEdit.setText(str(num))
        
    def get_zseries(self):
        num,ok = QtWidgets.QInputDialog.getInt(self,\
        "Number of Z-Series","enter a number",value=1,min=1)
        if str(num) != '':
            self.zseriesEdit.setText(str(num))
        
    def get_timepoint(self):
        num,ok = QtWidgets.QInputDialog.getInt(self,\
        "Number of Timepoints","enter a number",value=1,min=1)
        if str(num) != '':
            self.timepointEdit.setText(str(num))
        
    def get_name(self):
        text,ok = QtWidgets.QInputDialog.getText(self,\
        "Custom Name for Run","enter a name")
        if text != '':		
            self.nameEdit.setText(str(text))
        
    def start_convert(self):
        """Makes sure that user did not leave the input or output folder blank,
        then packs up all of the resources needed by the conversion program, 
        then locks the start button, the hands over control to the converter
        program
        """
        if str(self.folderEdit.text()) == '':
            self.folderEdit.setText('you must select a folder')
        elif str(self.folderEdit.text()) == 'you must select a folder':
            self.folderEdit.setText('')
        elif str(self.outfolderEdit.text()) == '':
            self.outfolderEdit.setText('you must select a folder')
        elif str(self.outfolderEdit.text()) == 'you must select a folder':
            self.outfolderEdit.setText('')
        else:
            params = []
            params.append(str(self.folderEdit.text()))
            params.append(str(self.outfolderEdit.text()))
            params.append(int(self.seriesEdit.text()))
            params.append(int(self.channelEdit.text()))
            params.append(int(self.zseriesEdit.text()))
            params.append(int(self.timepointEdit.text()))
            params.append(str(self.nameEdit.text()))
            params.append(str(self.usernotes.text()))
            params.append(str(self.ftypeEdit.text()))
            params.append(str(self.bffolderEdit.text()))
            print(params)
            self.run.setEnabled(False)
            converter(self,params)

    def open_help(self):
        self.hw = HelpWindowPopup()
        self.hw.show()

class HelpWindowPopup(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(HelpWindowPopup, self).__init__()
        self.popupUI()
        
    def popupUI(self):
        
        text = '\
Welcome to Batch Convert nd2 Files (Windows only)\n\
Below is a short description of what each of the buttons does, and credits:\
\n\n\
\
Folder to Convert - Opens dialog to select the folder containing your nd2 \
files. Subdirectories are not included.\n\
All nd2 files must have the same parameters. (number of series, channels, \
z-series, and timepoints)\n\n\
\
Output folder - The location that you want your newly created images to end \
up.\n\n\
\
Location of bftools - opens dialog to select location of the bftools folder. \
This should be included in the folder\n\
containing this script, but a new copy can be downloaded from: \n\
http://www.openmicroscopy.org/site/support/bio-formats5.1/users/comlinetools/\
\n\
Note: As of version 5.4.0 the newest versions do not work with nd2 files \
created by Nikon Elements AR software.\n\
Version 5.1.10 is the latest working version I have tested.\n\
Previous versions can be found at: \
http://downloads.openmicroscopy.org/bio-formats/\n\
To set up, extract the downloaded zip file and navigate to the newly created \
folder using the dialog created by the Location of bftools button.\n\n\
\
Series - The number of x/y locations in each well/slide/dish that were \
imaged.\n\n\
\
Z-series - The number of z planes (up and down) that were imaged at each \
xy point in series.\n\n\
\
Channels - The number of wavelengths measured at, usually the number of \
fluorophores used in the experiment.\n\n\
\
Timepoints - The number of images taken during a time course experiment.\n\n\
\
Run Name - The prefix which will be used for all files created. This can be \
set to any custom string.\n\
Leaving it blank will use the automatically generated unique ID for the \
run.\n\n\
\
Output Type - This is the file type which the converted files will be. Tiff \
is recommended because it is lossless,\n\
and so will not degrade your data. Look into compression methods of other \
formats before using.\n\n\
\
Notes - Whatever is written here will be recorded in the log file, which will \
be placed in the designated output folder.\n\n\
\
Set to Default - Records the input from each field described above (except \
Run Name, Output Type, and Notes)\n\
and fills it in any time this program is started up.\n\n\
\
Restore Default - Resets all fields to the state they were in at program \
initialization.\n\n\
\
Reset Defaults File - Deletes and re-makes the default save file with \
suggested, generic, values.\n\n\n\
\
Batch Convert nd2 Files was written by Tim Bates in the lab of Danica \
Fujimori at UCSF\n\
This program functions as a frontend for bfconvert, a command line program \
written by OME (The Open Microscopy Environment) in Java.\n\
More information about OME can be found at http://www.openmicroscopy.org/\
'
        
        pop = QtWidgets.QGridLayout()
        
        self.text = QtWidgets.QLabel(text)
        pop.addWidget(self.text,0,0)
        
        self.setLayout(pop)
        self.setWindowTitle('Batch Convert nd2 Files')    
        self.show()
        
def main():
    """ Just launches the gui, which in turn launches the converter...
    if everything else works as expected.
    """
    app = QtWidgets.QApplication(sys.argv)
    ex = UserInput()
    ex.show
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()