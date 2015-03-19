import sys
import time
import archiveclonesniffer.presenter as P

from PyQt5.QtCore import *
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from gui import auto_gui
from archiveclonesniffer import *
from threading import Thread

class ACSThread(Thread):
	def __init__(self, target, args, callback):
		Thread.__init__(self)
		self.callback = callback
		self.target = target
		self.args = args

	def run(self):
		result = self.target(*self.args)
		self.callback(result)

class Worker():
	def __init__(self):
		self.thread = Thread()

	def start(self, target, args):
		self.thread = ACSThread(target, args, self.update_viewport)
		showStatus('Processing ... please wait')
		self.thread.start()

	def update_viewport(self, result):
		ui.textEdit_viewport.append(result)
		#ui.textEdit_viewport.setPlainText(result) # causing program to hang ... warum?
		hideStatus()
		ui.textEdit_viewport.verticalScrollBar().setValue(0)

	def busy(self):
		if self.thread.isAlive():
			return True
		return False

def openFileDialog(func):
	def openDialog():
		lineEditElem, directory, filetypes = func()
		filename, type = QFileDialog.getOpenFileName(MainWindow, directory=directory, filter=filetypes)
		lineEditElem.setText(filename)
		return filename
	return openDialog

@openFileDialog
def handle_DBSelect():
	directory, filetypes = (".", "Sqlite Database (*.sqlite *.sqlite3 *.db *.db3);; All Files (*.*)")
	return(ui.lineEdit_dbname, directory, filetypes)

@openFileDialog
def handle_archiveSelect():
	directory, filetypes = (".", "Zip/RAR archive (*.zip *.rar);; All Files (*.*)")
	return(ui.lineEdit_archive, directory, filetypes)

@openFileDialog
def handle_archive2Select():
	directory, filetypes = (".", "Zip/RAR archive (*.zip *.rar);; All Files (*.*)")
	return(ui.lineEdit_archive2, directory, filetypes)

@openFileDialog
def handle_fileSelect():
	directory, filetypes = (".", "All Files (*.*);; Image Files (*.jpg *.jpeg *.png *.gif *.bmp)")
	return(ui.lineEdit_files, directory, filetypes)

def get_max_text_area_width():
    font_width = QFontMetrics(monospace_font).width('a')
    widget_width = textArea.width()
    max_chars_in_line = int(widget_width/font_width) - 1
    return max_chars_in_line

def none_if_empty_str(arg):
	stripped_arg = arg.strip()
	if stripped_arg == "":
		return None
	return arg.strip()

def handle_compare():
	db = none_if_empty_str(ui.lineEdit_dbname.text())
	archive = none_if_empty_str(ui.lineEdit_archive.text())
	archive2 = none_if_empty_str(ui.lineEdit_archive2.text())
	files = none_if_empty_str(ui.lineEdit_files.text())
	file_list = None if files is None else files.split(' ')
	textArea.clear()
	#textArea.setPlainText("\u25A0 Comparing ... ")
	#QApplication.processEvents()
	#P.do_comparison, ((db, file_list, archive, archive2))
	t = background_worker.start(target=P.do_comparison, args=(db, file_list, archive, archive2))
	#hideStatus()
	#textArea.setPlainText("Completed in - {}\n\n".format(time.strftime ("%H:%M:%Ss", time.gmtime(t1-t0))))
	#textArea.append(result)
	#textArea.verticalScrollBar().setValue(0)

def handle_list():
	database = ui.lineEdit_dbname.text()
	archive  = ui.lineEdit_archive.text()
	db_basename =  os.path.basename(database)
	archive_basename = os.path.basename(archive)
	textArea.clear()
	#text = P.list_archive_contents(archive, database)
	#textArea.append(text)
	t = background_worker.start(target=P.list_archive_contents, args=(archive, database))

def handle_add():
	database = ui.lineEdit_dbname.text()
	archive  = ui.lineEdit_archive.text()
	db_basename =  os.path.basename(database)
	archive_basename = os.path.basename(archive)
	force_add_flag = ui.checkBox_forceAdd.isChecked()
	textArea.clear()
	t = background_worker.start(target=P.add_archive_to_db, args=(archive, database, force_add_flag))
	#text = P.add_archive_to_db(archive, database, force_add_flag)


def handle_remove():
	database = ui.lineEdit_dbname.text()
	archive  = ui.lineEdit_archive.text()
	db_basename =  os.path.basename(database)
	archive_basename = os.path.basename(archive)
	force_add_flag = ui.checkBox_forceAdd.isChecked()
	text = P.delete_archive_from_db(archive_basename, database)
	textArea.setPlainText(text)

def handle_reset():
	value = get_confirmation("Warning! Resetting will clear database of stored contents.", "Do you really wish to reset database?")
	db = ui.lineEdit_dbname.text().strip()
	result = P.reset_db(db)
	textArea.setPlainText(result)

def backup_file_if_exists(file):
	if os.path.exists(file):
		#backup_file = file + ".backup"
		#while os.path.exists(backup_file):
		#	backup_file += ".backup"
		#os.rename(file, backup_file)
		message = "'{}' already exists. Will create backup\n".format(file)
		message += P.backup_database(file)
		return True, message
	return False, ""

def create_new_database():
	dbname, type = QFileDialog.getSaveFileName(MainWindow, caption="Create New Database", directory=".", filter="Sqlite Database (*.sqlite)")
	if dbname == '':
		return
	textArea.clear()
	if os.path.exists(dbname):
		status, message = backup_file_if_exists(dbname)
		if status == True:
			textArea.append(message)
	ui.lineEdit_dbname.setText(dbname)
	textArea.append("Attempting to create SQLite database '{}'\n".format(dbname))
	output = P.create_db(dbname)
	textArea.append(output)

def create_backup():
	database = ui.lineEdit_dbname.text()
	if database.strip() == "":
		show_messageBox("Database name empty", "You need to choose an SQLite database first")
		focus_field_and_highlight(ui.lineEdit_dbname)
	else:
		result = P.backup_database(database)
		textArea.setPlainText(result)

def handle_sql_query():
	db = ui.lineEdit_dbname.text()
	sql_query = ui.plainTextEdit_sql.toPlainText()
	if db.strip() == "":
		show_messageBox("Database name empty", "Please select a SQLite database to perform query on")
		focus_field_and_highlight(ui.lineEdit_dbname)
	elif sql_query.strip() == "":
		show_messageBox("SQL query is empty", "No results for you!")
	else:
		textArea.clear()
		t = background_worker.start(target=P.run_sql_query, args=(db,sql_query))
		#textArea.setPlainText(result)

def get_confirmation(msg, action_msg):
	msgBox = QMessageBox()
	msgBox.setIcon(QMessageBox.Warning)
	msgBox.setWindowIcon(MainWindow.windowIcon())
	msgBox.setText(msg)
	msgBox.setInformativeText(action_msg)
	msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
	msgBox.setDefaultButton(QMessageBox.No)
	value = msgBox.exec()
	if value == QMessageBox.No:
		return False
	if value == QMessageBox.Yes:
		return True

def show_messageBox(msg, action_msg):
	msgBox = QMessageBox()
	msgBox.setIcon(QMessageBox.Warning)
	msgBox.setWindowIcon(MainWindow.windowIcon())
	msgBox.setText(msg)
	msgBox.setInformativeText(action_msg)
	msgBox.setStandardButtons(QMessageBox.Ok)
	msgBox.exec()

def showStatus(msg):
	styledMsg = "<span style='margin-right:20px'>" + msg + "</span>"
	statusLabel.show()
	progressBar.show()
	statusLabel.setText(styledMsg)

def hideStatus():
	statusLabel.setText('')
	statusLabel.hide()
	progressBar.hide()

# def handle_radioButtons():
# 	updateStatusBar()

def handle_execute():
	if background_worker.busy():
		show_messageBox("Application Busy", "Please wait until current operation is completed")
		return

	if ui.tabWidget.currentIndex() == ui.tabWidget.indexOf(ui.tab_main):
		handler = {
			ui.radioButton_compare  : handle_compare,
			ui.radioButton_list     : handle_list,
			ui.radioButton_add      : handle_add,
			ui.radioButton_remove   : handle_remove,
			ui.radioButton_reset    : handle_reset
		}
		# Call handler for selected operation
		op = ui.buttonGroup_ops.checkedButton()
		if op == None:
			show_messageBox("No operation selected", "You must select and operation to perform first")
			return
		handler[op]()
	else:
		handle_sql_query()

def handle_drag(e):
	e.accept()

def handle_main_window_drop(e):
	data = e.mimeData()
	if data.hasUrls():
		urls = data.urls()
		for url in urls:
			if url.isLocalFile():
				file = QFileInfo(url.toLocalFile())
				extension = file.suffix()
				if extension == "sqlite" or extension == "sqlite3" or extension == "db" or extension == "db3":
					ui.lineEdit_dbname.setText(file.absoluteFilePath())
				elif extension == "zip" or extension == "rar":
					ui.lineEdit_archive.setText(file.absoluteFilePath())
				else:
					ui.lineEdit_files.setText(file.absoluteFilePath())

def handle_archive2_drop(e):
	print ("Archive2 Drop event")
	data = e.mimeData()
	if data.hasUrls():
		urls = data.urls()
		for url in urls:
			if url.isLocalFile():
				file = QFileInfo(url.toLocalFile())
				extension = file.suffix()
				if extension == "zip" or extension == "rar":
					ui.lineEdit_archive2.setText(file.absoluteFilePath())

def handle_view_schema():
	db = ui.lineEdit_dbname.text()
	if db.strip() == "":
		show_messageBox("Database name empty", "Please select a SQLite database to perform query on")
		focus_field_and_highlight(ui.lineEdit_dbname)
	else:
		schema_text = P.get_database_schema(db)
		textArea.setPlainText(schema_text)

@pyqtSlot(QWidget)
def focus_field_and_highlight(widget):
	ui.tabWidget.setCurrentIndex(ui.tabWidget.indexOf(ui.tab_main))
	if widget == ui.plainTextEdit_sql:
		ui.tabWidget.setCurrentIndex(ui.tabWidget.indexOf(ui.tab_sql))
	widget.setFocus()
	widget.selectAll()

def clear_all_fields():
	ui.lineEdit_dbname.setText("")
	ui.lineEdit_archive.setText("")
	ui.lineEdit_archive2.setText("")
	ui.lineEdit_files.setText("")
	ui.plainTextEdit_sql.setPlainText("")
	textArea.setPlainText("")

def show_about_dialog():
	box = QMessageBox()
	help_str = """
	<b> About Archive Clone Sniffer</b>
	<br>2015<br>
	<p>by iMad</p>
	<p><u>Keyboard Shortcuts</u></p>
	<p>
		<i>Ctrl + 1-5</i> : Edit database, archive, archive2,file or SQL query fields<br>
		<i>Ctrl + Q </i>: Quit ACS<br>
		<i>Ctrl + N </i>: Create New Database<br>
		<i>Ctrl + Alt + C </i>: Clear all text input and output fields<br><br>
		Press and hold Alt key to show various underlined shortcuts<br>
		Drag and drop Sqlite / Archive files to fill respective fields. Other file types go to the files field.
	</p>
	<p>
		Built using <a href="http://www.riverbankcomputing.com/software/pyqt/intro">PyQt5</a> on
					<a href="https://www.python.org/">Python3</a> and
					<a href="http://www.sqlite.org/">SQLite</a><br>
		Uses icons from <a href="http://openclipart.org">OpenClipArt</a>
	</p>
	"""
	box.about(MainWindow,"About", help_str)

MAX_TABLE_WIDTH = 0;
LINE_CHAR = '\u2500' # Box drawing character '─'

qt_app = QApplication(sys.argv)

MainWindow = QMainWindow()
ui = auto_gui.Ui_MainWindow()
ui.setupUi(MainWindow)
background_worker = Worker()

# Set window height and width to 75% of the screen size
resolution = QApplication.desktop().screenGeometry()
w_width = int(0.75 * resolution.width())
w_height = int(w_width * resolution.height() / resolution.width())
MainWindow.resize(w_width, w_height)

MainWindow.show()

ui.lineEdit_dbname.clearButtonEnabled = True;
#ui.buttonGroup_ops.buttonClicked.connect(handle_radioButtons)
ui.pushButton_exec.clicked.connect(handle_execute)
ui.pushButton_viewSchema.clicked.connect(handle_view_schema)

ui.toolSelectButton_db.clicked.connect(handle_DBSelect)
ui.toolSelectButton_archive.clicked.connect(handle_archiveSelect)
ui.toolSelectButton_archive2.clicked.connect(handle_archive2Select)
ui.toolSelectButton_file.clicked.connect(handle_fileSelect)

monospace_font = QFont("Cousine")
monospace_font.setPointSize(11)
#monospace_font.setWeight(55)
monospace_font.setStyleHint(QFont.Monospace)
textArea = ui.textEdit_viewport
textArea.setFont(monospace_font)
textArea.setReadOnly(True)

statusLabel = QLabel()
progressBar = QProgressBar()
ui.statusbar.addWidget(statusLabel)
statusBar_spacer = QSpacerItem(10,10,QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
#ui.statusbar.addWidget(statusBar_spacer)
ui.statusbar.addWidget(progressBar)
progressBar.move(100,0)
progressBar.setMinimum(0)
progressBar.setMaximum(0)
progressBar.setTextVisible(False)
progressBar.setMaximumHeight(ui.statusbar.height())
progressBar.setMaximumWidth(ui.statusbar.width()/4)
statusLabel.hide()
progressBar.hide()

######################## Capturing KB shortcuts with signal mapper ###########################
# 1. Define each shortcut and set it's context
shortcut_ctrl_1 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_1), MainWindow) #, focus_lineEdit)
shortcut_ctrl_1.setContext(Qt.ApplicationShortcut)
#shortcut.activated.connect(signalMapper.map())
shortcut_ctrl_2 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_2), MainWindow) #, focus_lineEdit)
shortcut_ctrl_2.setContext(Qt.ApplicationShortcut)
shortcut_ctrl_3 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_3), MainWindow) #, focus_lineEdit)
shortcut_ctrl_3.setContext(Qt.ApplicationShortcut)
shortcut_ctrl_4 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_4), MainWindow) #, focus_lineEdit)
shortcut_ctrl_4.setContext(Qt.ApplicationShortcut)
shortcut_ctrl_5 = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_5), MainWindow) #, focus_lineEdit)
shortcut_ctrl_5.setContext(Qt.ApplicationShortcut)

# 2. Define a signal wrapper and map each shortcut to the widget to focus on
signalMapper = QSignalMapper(MainWindow)
signalMapper.setMapping(shortcut_ctrl_1, ui.lineEdit_dbname)
signalMapper.setMapping(shortcut_ctrl_2, ui.lineEdit_archive)
signalMapper.setMapping(shortcut_ctrl_3, ui.lineEdit_archive2)
signalMapper.setMapping(shortcut_ctrl_4, ui.lineEdit_files)
signalMapper.setMapping(shortcut_ctrl_5, ui.plainTextEdit_sql)

# 3. Connect the SIGNAL(activate()) of each shortcut to the signal mapper
shortcut_ctrl_1.activated.connect(signalMapper.map)
shortcut_ctrl_2.activated.connect(signalMapper.map)
shortcut_ctrl_3.activated.connect(signalMapper.map)
shortcut_ctrl_4.activated.connect(signalMapper.map)
shortcut_ctrl_5.activated.connect(signalMapper.map)

# 4. And map the signal mapper to the SLOT(pressed())
# take care to specify the return type (QWidget) in both in mapped and in the SLOT decorator
signalMapper.mapped[(QWidget)].connect(focus_field_and_highlight)

##################################################################################################


MainWindow.dragEnterEvent = handle_drag
MainWindow.dropEvent = handle_main_window_drop

ui.lineEdit_archive2.dragEnterEvent = handle_drag
ui.lineEdit_archive2.dropEvent = handle_archive2_drop

ui.action_New.triggered.connect(create_new_database)
ui.action_Backup_Database.triggered.connect(create_backup)
ui.actionE_xit.triggered.connect(qApp.quit)
ui.action_Clear_All_Fields.triggered.connect(clear_all_fields)
ui.action_About.triggered.connect(show_about_dialog)

sys.exit(qt_app.exec_())


# TODO
# status for processing and add incl. stats
# size of backup
