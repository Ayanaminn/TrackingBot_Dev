# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainGUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1311, 863)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setEnabled(True)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 1311, 841))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(8)
        font.setBold(True)
        font.setWeight(75)
        self.tabWidget.setFont(font)
        self.tabWidget.setStyleSheet("QTabWidget::pane {\n"
"  border: 1px solid lightgray;\n"
"  top:-1px; \n"
"  background:rgb(208, 208, 208);; \n"
"} \n"
"\n"
"QTabBar::tab {\n"
"  background: rgb(230, 230, 230);  \n"
"  height:13px;\n"
"  width: 80px;\n"
"  border: 1px solid lightgray; \n"
"  padding: 7px;\n"
"} \n"
"\n"
"QTabBar::tab:selected { \n"
"  background: rgb(85, 170, 255); \n"
"  margin-bottom: -1px; \n"
"}")
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tabWidget.setIconSize(QtCore.QSize(16, 16))
        self.tabWidget.setDocumentMode(False)
        self.tabWidget.setObjectName("tabWidget")
        self.menuTab = QtWidgets.QWidget()
        self.menuTab.setObjectName("menuTab")
        self.label = QtWidgets.QLabel(self.menuTab)
        self.label.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.label.setFrameShape(QtWidgets.QFrame.Box)
        self.label.setText("")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.localModeButton = QtWidgets.QPushButton(self.menuTab)
        self.localModeButton.setGeometry(QtCore.QRect(240, 230, 211, 111))
        font = QtGui.QFont()
        font.setFamily("Arial Black")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.localModeButton.setFont(font)
        self.localModeButton.setObjectName("localModeButton")
        self.liveModeButton = QtWidgets.QPushButton(self.menuTab)
        self.liveModeButton.setGeometry(QtCore.QRect(560, 230, 211, 111))
        font = QtGui.QFont()
        font.setFamily("Arial Black")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.liveModeButton.setFont(font)
        self.liveModeButton.setObjectName("liveModeButton")
        self.tabWidget.addTab(self.menuTab, "")
        self.loadVidTab = QtWidgets.QWidget()
        self.loadVidTab.setObjectName("loadVidTab")
        self.VBoxLabel = QtWidgets.QLabel(self.loadVidTab)
        self.VBoxLabel.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.VBoxLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.VBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.VBoxLabel.setObjectName("VBoxLabel")
        self.loadVidButton = QtWidgets.QPushButton(self.loadVidTab)
        self.loadVidButton.setGeometry(QtCore.QRect(410, 210, 211, 171))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.loadVidButton.setFont(font)
        self.loadVidButton.setObjectName("loadVidButton")
        self.loadImgButton = QtWidgets.QPushButton(self.loadVidTab)
        self.loadImgButton.setGeometry(QtCore.QRect(1040, 240, 71, 31))
        self.loadImgButton.setObjectName("loadImgButton")
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.loadVidTab)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 580, 1021, 51))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.vidSliderLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.vidSliderLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.vidSliderLayout.setContentsMargins(5, 0, 5, 0)
        self.vidSliderLayout.setSpacing(6)
        self.vidSliderLayout.setObjectName("vidSliderLayout")
        self.playButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.playButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.playButton.sizePolicy().hasHeightForWidth())
        self.playButton.setSizePolicy(sizePolicy)
        self.playButton.setMinimumSize(QtCore.QSize(0, 0))
        self.playButton.setMaximumSize(QtCore.QSize(35, 35))
        self.playButton.setText("")
        self.playButton.setObjectName("playButton")
        self.vidSliderLayout.addWidget(self.playButton)
        self.stopButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.stopButton.setEnabled(False)
        self.stopButton.setMaximumSize(QtCore.QSize(35, 35))
        self.stopButton.setText("")
        self.stopButton.setObjectName("stopButton")
        self.vidSliderLayout.addWidget(self.stopButton)
        self.vidPosLabel = QtWidgets.QLabel(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.vidPosLabel.setFont(font)
        self.vidPosLabel.setObjectName("vidPosLabel")
        self.vidSliderLayout.addWidget(self.vidPosLabel)
        self.vidProgressBar = QtWidgets.QSlider(self.horizontalLayoutWidget)
        self.vidProgressBar.setEnabled(False)
        self.vidProgressBar.setMaximumSize(QtCore.QSize(900, 16777215))
        self.vidProgressBar.setOrientation(QtCore.Qt.Horizontal)
        self.vidProgressBar.setObjectName("vidProgressBar")
        self.vidSliderLayout.addWidget(self.vidProgressBar)
        self.vidLenLabel = QtWidgets.QLabel(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.vidLenLabel.setFont(font)
        self.vidLenLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.vidLenLabel.setObjectName("vidLenLabel")
        self.vidSliderLayout.addWidget(self.vidLenLabel)
        self.vidNameLabel = QtWidgets.QLabel(self.loadVidTab)
        self.vidNameLabel.setGeometry(QtCore.QRect(1040, 10, 61, 51))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.vidNameLabel.setFont(font)
        self.vidNameLabel.setObjectName("vidNameLabel")
        self.vidDurLabel = QtWidgets.QLabel(self.loadVidTab)
        self.vidDurLabel.setGeometry(QtCore.QRect(1040, 70, 181, 41))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.vidDurLabel.setFont(font)
        self.vidDurLabel.setObjectName("vidDurLabel")
        self.vidFpsLabel = QtWidgets.QLabel(self.loadVidTab)
        self.vidFpsLabel.setGeometry(QtCore.QRect(1040, 120, 121, 51))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.vidFpsLabel.setFont(font)
        self.vidFpsLabel.setObjectName("vidFpsLabel")
        self.vidResLabel = QtWidgets.QLabel(self.loadVidTab)
        self.vidResLabel.setGeometry(QtCore.QRect(1040, 170, 91, 51))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.vidResLabel.setFont(font)
        self.vidResLabel.setObjectName("vidResLabel")
        self.loadNewVidButton = QtWidgets.QPushButton(self.loadVidTab)
        self.loadNewVidButton.setEnabled(False)
        self.loadNewVidButton.setGeometry(QtCore.QRect(1234, 20, 61, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.loadNewVidButton.setFont(font)
        self.loadNewVidButton.setObjectName("loadNewVidButton")
        self.caliTabLinkButton = QtWidgets.QCommandLinkButton(self.loadVidTab)
        self.caliTabLinkButton.setEnabled(False)
        self.caliTabLinkButton.setGeometry(QtCore.QRect(1140, 730, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.caliTabLinkButton.setFont(font)
        self.caliTabLinkButton.setObjectName("caliTabLinkButton")
        self.vidNameText = QtWidgets.QLabel(self.loadVidTab)
        self.vidNameText.setGeometry(QtCore.QRect(1110, 20, 121, 31))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.vidNameText.sizePolicy().hasHeightForWidth())
        self.vidNameText.setSizePolicy(sizePolicy)
        self.vidNameText.setText("")
        self.vidNameText.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.vidNameText.setWordWrap(True)
        self.vidNameText.setObjectName("vidNameText")
        self.vidDurText = QtWidgets.QLabel(self.loadVidTab)
        self.vidDurText.setGeometry(QtCore.QRect(1230, 70, 81, 41))
        self.vidDurText.setText("")
        self.vidDurText.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.vidDurText.setObjectName("vidDurText")
        self.vidFpsText = QtWidgets.QLabel(self.loadVidTab)
        self.vidFpsText.setGeometry(QtCore.QRect(1160, 130, 101, 31))
        self.vidFpsText.setText("")
        self.vidFpsText.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.vidFpsText.setObjectName("vidFpsText")
        self.vidResText = QtWidgets.QLabel(self.loadVidTab)
        self.vidResText.setGeometry(QtCore.QRect(1120, 180, 101, 31))
        self.vidResText.setText("")
        self.vidResText.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.vidResText.setObjectName("vidResText")
        self.tabWidget.addTab(self.loadVidTab, "")
        self.caliTab = QtWidgets.QWidget()
        self.caliTab.setObjectName("caliTab")
        self.caliBoxLabel = QtWidgets.QLabel(self.caliTab)
        self.caliBoxLabel.setEnabled(False)
        self.caliBoxLabel.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.caliBoxLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.caliBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.caliBoxLabel.setObjectName("caliBoxLabel")
        self.metricNumInput = QtWidgets.QLineEdit(self.caliTab)
        self.metricNumInput.setEnabled(False)
        self.metricNumInput.setGeometry(QtCore.QRect(1170, 80, 91, 31))
        self.metricNumInput.setInputMask("")
        self.metricNumInput.setClearButtonEnabled(False)
        self.metricNumInput.setObjectName("metricNumInput")
        self.caliUnitLabel = QtWidgets.QLabel(self.caliTab)
        self.caliUnitLabel.setGeometry(QtCore.QRect(1270, 90, 47, 13))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.caliUnitLabel.setFont(font)
        self.caliUnitLabel.setObjectName("caliUnitLabel")
        self.caliTabText1 = QtWidgets.QLabel(self.caliTab)
        self.caliTabText1.setGeometry(QtCore.QRect(1030, 80, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.caliTabText1.setFont(font)
        self.caliTabText1.setAlignment(QtCore.Qt.AlignCenter)
        self.caliTabText1.setObjectName("caliTabText1")
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(self.caliTab)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(1050, 10, 231, 41))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(50)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.drawScaleButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.drawScaleButton.sizePolicy().hasHeightForWidth())
        self.drawScaleButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.drawScaleButton.setFont(font)
        self.drawScaleButton.setObjectName("drawScaleButton")
        self.horizontalLayout.addWidget(self.drawScaleButton)
        self.resetScaleButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.resetScaleButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resetScaleButton.sizePolicy().hasHeightForWidth())
        self.resetScaleButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.resetScaleButton.setFont(font)
        self.resetScaleButton.setObjectName("resetScaleButton")
        self.horizontalLayout.addWidget(self.resetScaleButton)
        self.applyScaleButton = QtWidgets.QPushButton(self.caliTab)
        self.applyScaleButton.setEnabled(False)
        self.applyScaleButton.setGeometry(QtCore.QRect(1170, 140, 89, 39))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.applyScaleButton.sizePolicy().hasHeightForWidth())
        self.applyScaleButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.applyScaleButton.setFont(font)
        self.applyScaleButton.setObjectName("applyScaleButton")
        self.threTabLinkButton = QtWidgets.QCommandLinkButton(self.caliTab)
        self.threTabLinkButton.setEnabled(False)
        self.threTabLinkButton.setGeometry(QtCore.QRect(1160, 750, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.threTabLinkButton.setFont(font)
        self.threTabLinkButton.setObjectName("threTabLinkButton")
        self.tabWidget.addTab(self.caliTab, "")
        self.threTab = QtWidgets.QWidget()
        self.threTab.setObjectName("threTab")
        self.threBoxLabel = QtWidgets.QLabel(self.threTab)
        self.threBoxLabel.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.threBoxLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.threBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.threBoxLabel.setObjectName("threBoxLabel")
        self.horizontalLayoutWidget_3 = QtWidgets.QWidget(self.threTab)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(1030, 50, 231, 31))
        self.horizontalLayoutWidget_3.setObjectName("horizontalLayoutWidget_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(80)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.threTabText1 = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.threTabText1.setFont(font)
        self.threTabText1.setAlignment(QtCore.Qt.AlignCenter)
        self.threTabText1.setObjectName("threTabText1")
        self.horizontalLayout_2.addWidget(self.threTabText1)
        self.objNumBox = QtWidgets.QSpinBox(self.horizontalLayoutWidget_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.objNumBox.sizePolicy().hasHeightForWidth())
        self.objNumBox.setSizePolicy(sizePolicy)
        self.objNumBox.setSuffix("")
        self.objNumBox.setMinimum(1)
        self.objNumBox.setObjectName("objNumBox")
        self.horizontalLayout_2.addWidget(self.objNumBox)
        self.horizontalLayoutWidget_4 = QtWidgets.QWidget(self.threTab)
        self.horizontalLayoutWidget_4.setGeometry(QtCore.QRect(1030, 240, 271, 111))
        self.horizontalLayoutWidget_4.setObjectName("horizontalLayoutWidget_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.cntMaxSlider = QtWidgets.QSlider(self.horizontalLayoutWidget_4)
        self.cntMaxSlider.setOrientation(QtCore.Qt.Horizontal)
        self.cntMaxSlider.setObjectName("cntMaxSlider")
        self.verticalLayout.addWidget(self.cntMaxSlider)
        self.cntMinSlider = QtWidgets.QSlider(self.horizontalLayoutWidget_4)
        self.cntMinSlider.setOrientation(QtCore.Qt.Horizontal)
        self.cntMinSlider.setObjectName("cntMinSlider")
        self.verticalLayout.addWidget(self.cntMinSlider)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.threTabText2 = QtWidgets.QLabel(self.horizontalLayoutWidget_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.threTabText2.sizePolicy().hasHeightForWidth())
        self.threTabText2.setSizePolicy(sizePolicy)
        self.threTabText2.setAlignment(QtCore.Qt.AlignCenter)
        self.threTabText2.setObjectName("threTabText2")
        self.verticalLayout_2.addWidget(self.threTabText2)
        self.cntMaxSpin = QtWidgets.QSpinBox(self.horizontalLayoutWidget_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cntMaxSpin.sizePolicy().hasHeightForWidth())
        self.cntMaxSpin.setSizePolicy(sizePolicy)
        self.cntMaxSpin.setMaximum(9999)
        self.cntMaxSpin.setObjectName("cntMaxSpin")
        self.verticalLayout_2.addWidget(self.cntMaxSpin)
        self.threTabText3 = QtWidgets.QLabel(self.horizontalLayoutWidget_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.threTabText3.sizePolicy().hasHeightForWidth())
        self.threTabText3.setSizePolicy(sizePolicy)
        self.threTabText3.setAlignment(QtCore.Qt.AlignCenter)
        self.threTabText3.setObjectName("threTabText3")
        self.verticalLayout_2.addWidget(self.threTabText3)
        self.cntMinSpin = QtWidgets.QSpinBox(self.horizontalLayoutWidget_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cntMinSpin.sizePolicy().hasHeightForWidth())
        self.cntMinSpin.setSizePolicy(sizePolicy)
        self.cntMinSpin.setMaximum(9998)
        self.cntMinSpin.setObjectName("cntMinSpin")
        self.verticalLayout_2.addWidget(self.cntMinSpin)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.threTabText4 = QtWidgets.QLabel(self.threTab)
        self.threTabText4.setGeometry(QtCore.QRect(1020, 220, 81, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.threTabText4.setFont(font)
        self.threTabText4.setAlignment(QtCore.Qt.AlignCenter)
        self.threTabText4.setObjectName("threTabText4")
        self.threTabText5 = QtWidgets.QLabel(self.threTab)
        self.threTabText5.setGeometry(QtCore.QRect(1020, 90, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.threTabText5.setFont(font)
        self.threTabText5.setAlignment(QtCore.Qt.AlignCenter)
        self.threTabText5.setObjectName("threTabText5")
        self.threTabText6 = QtWidgets.QLabel(self.threTab)
        self.threTabText6.setGeometry(QtCore.QRect(1020, 150, 51, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.threTabText6.setFont(font)
        self.threTabText6.setAlignment(QtCore.Qt.AlignCenter)
        self.threTabText6.setObjectName("threTabText6")
        self.blockSizeSlider = QtWidgets.QSlider(self.threTab)
        self.blockSizeSlider.setGeometry(QtCore.QRect(1030, 120, 211, 22))
        self.blockSizeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.blockSizeSlider.setObjectName("blockSizeSlider")
        self.blockSizeSpin = QtWidgets.QSpinBox(self.threTab)
        self.blockSizeSpin.setGeometry(QtCore.QRect(1250, 120, 51, 22))
        self.blockSizeSpin.setObjectName("blockSizeSpin")
        self.offsetSlider = QtWidgets.QSlider(self.threTab)
        self.offsetSlider.setGeometry(QtCore.QRect(1030, 180, 211, 22))
        self.offsetSlider.setOrientation(QtCore.Qt.Horizontal)
        self.offsetSlider.setObjectName("offsetSlider")
        self.offsetSpin = QtWidgets.QSpinBox(self.threTab)
        self.offsetSpin.setGeometry(QtCore.QRect(1250, 170, 51, 22))
        self.offsetSpin.setObjectName("offsetSpin")
        self.applyThreButton = QtWidgets.QPushButton(self.threTab)
        self.applyThreButton.setGeometry(QtCore.QRect(1050, 580, 89, 39))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.applyThreButton.sizePolicy().hasHeightForWidth())
        self.applyThreButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.applyThreButton.setFont(font)
        self.applyThreButton.setObjectName("applyThreButton")
        self.resetThreButton = QtWidgets.QPushButton(self.threTab)
        self.resetThreButton.setGeometry(QtCore.QRect(1210, 580, 89, 39))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.resetThreButton.sizePolicy().hasHeightForWidth())
        self.resetThreButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.resetThreButton.setFont(font)
        self.resetThreButton.setObjectName("resetThreButton")
        self.applyMaskcheckBox = QtWidgets.QCheckBox(self.threTab)
        self.applyMaskcheckBox.setGeometry(QtCore.QRect(1030, 410, 111, 17))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.applyMaskcheckBox.setFont(font)
        self.applyMaskcheckBox.setObjectName("applyMaskcheckBox")
        self.invertCtrcheckBox = QtWidgets.QCheckBox(self.threTab)
        self.invertCtrcheckBox.setGeometry(QtCore.QRect(1030, 490, 111, 17))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.invertCtrcheckBox.setFont(font)
        self.invertCtrcheckBox.setObjectName("invertCtrcheckBox")
        self.threTabText7 = QtWidgets.QLabel(self.threTab)
        self.threTabText7.setGeometry(QtCore.QRect(1030, 0, 171, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.threTabText7.setFont(font)
        self.threTabText7.setObjectName("threTabText7")
        self.horizontalLayoutWidget_5 = QtWidgets.QWidget(self.threTab)
        self.horizontalLayoutWidget_5.setGeometry(QtCore.QRect(0, 580, 1021, 51))
        self.horizontalLayoutWidget_5.setObjectName("horizontalLayoutWidget_5")
        self.threSliderLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_5)
        self.threSliderLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.threSliderLayout.setContentsMargins(5, 0, 5, 0)
        self.threSliderLayout.setSpacing(6)
        self.threSliderLayout.setObjectName("threSliderLayout")
        self.threPlayButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_5)
        self.threPlayButton.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.threPlayButton.sizePolicy().hasHeightForWidth())
        self.threPlayButton.setSizePolicy(sizePolicy)
        self.threPlayButton.setMinimumSize(QtCore.QSize(0, 0))
        self.threPlayButton.setMaximumSize(QtCore.QSize(35, 35))
        self.threPlayButton.setText("")
        self.threPlayButton.setObjectName("threPlayButton")
        self.threSliderLayout.addWidget(self.threPlayButton)
        self.threStopButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_5)
        self.threStopButton.setEnabled(True)
        self.threStopButton.setMaximumSize(QtCore.QSize(35, 35))
        self.threStopButton.setText("")
        self.threStopButton.setObjectName("threStopButton")
        self.threSliderLayout.addWidget(self.threStopButton)
        self.threPosLabel = QtWidgets.QLabel(self.horizontalLayoutWidget_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.threPosLabel.setFont(font)
        self.threPosLabel.setObjectName("threPosLabel")
        self.threSliderLayout.addWidget(self.threPosLabel)
        self.threProgressBar = QtWidgets.QSlider(self.horizontalLayoutWidget_5)
        self.threProgressBar.setEnabled(True)
        self.threProgressBar.setMaximumSize(QtCore.QSize(900, 16777215))
        self.threProgressBar.setOrientation(QtCore.Qt.Horizontal)
        self.threProgressBar.setObjectName("threProgressBar")
        self.threSliderLayout.addWidget(self.threProgressBar)
        self.threLenLabel = QtWidgets.QLabel(self.horizontalLayoutWidget_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.threLenLabel.setFont(font)
        self.threLenLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.threLenLabel.setObjectName("threLenLabel")
        self.threSliderLayout.addWidget(self.threLenLabel)
        self.trackTabLinkButton = QtWidgets.QCommandLinkButton(self.threTab)
        self.trackTabLinkButton.setEnabled(False)
        self.trackTabLinkButton.setGeometry(QtCore.QRect(1159, 750, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.trackTabLinkButton.setFont(font)
        self.trackTabLinkButton.setObjectName("trackTabLinkButton")
        self.tabWidget.addTab(self.threTab, "")
        self.trackinTab = QtWidgets.QWidget()
        self.trackinTab.setObjectName("trackinTab")
        self.trackingeBoxLabel = QtWidgets.QLabel(self.trackinTab)
        self.trackingeBoxLabel.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.trackingeBoxLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.trackingeBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.trackingeBoxLabel.setObjectName("trackingeBoxLabel")
        self.horizontalLayoutWidget_6 = QtWidgets.QWidget(self.trackinTab)
        self.horizontalLayoutWidget_6.setGeometry(QtCore.QRect(0, 580, 1021, 51))
        self.horizontalLayoutWidget_6.setObjectName("horizontalLayoutWidget_6")
        self.trackSliderLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_6)
        self.trackSliderLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.trackSliderLayout.setContentsMargins(5, 0, 5, 0)
        self.trackSliderLayout.setSpacing(6)
        self.trackSliderLayout.setObjectName("trackSliderLayout")
        self.trackStartButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_6)
        self.trackStartButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.trackStartButton.sizePolicy().hasHeightForWidth())
        self.trackStartButton.setSizePolicy(sizePolicy)
        self.trackStartButton.setMinimumSize(QtCore.QSize(0, 0))
        self.trackStartButton.setMaximumSize(QtCore.QSize(35, 35))
        self.trackStartButton.setText("")
        self.trackStartButton.setObjectName("trackStartButton")
        self.trackSliderLayout.addWidget(self.trackStartButton)
        self.trackStopButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_6)
        self.trackStopButton.setEnabled(False)
        self.trackStopButton.setMaximumSize(QtCore.QSize(35, 35))
        self.trackStopButton.setText("")
        self.trackStopButton.setObjectName("trackStopButton")
        self.trackSliderLayout.addWidget(self.trackStopButton)
        self.trackPosLabel = QtWidgets.QLabel(self.horizontalLayoutWidget_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.trackPosLabel.setFont(font)
        self.trackPosLabel.setObjectName("trackPosLabel")
        self.trackSliderLayout.addWidget(self.trackPosLabel)
        self.vidProgressBar_3 = QtWidgets.QSlider(self.horizontalLayoutWidget_6)
        self.vidProgressBar_3.setEnabled(False)
        self.vidProgressBar_3.setMaximumSize(QtCore.QSize(900, 16777215))
        self.vidProgressBar_3.setOrientation(QtCore.Qt.Horizontal)
        self.vidProgressBar_3.setObjectName("vidProgressBar_3")
        self.trackSliderLayout.addWidget(self.vidProgressBar_3)
        self.trackLenLabel = QtWidgets.QLabel(self.horizontalLayoutWidget_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.trackLenLabel.setFont(font)
        self.trackLenLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.trackLenLabel.setObjectName("trackLenLabel")
        self.trackSliderLayout.addWidget(self.trackLenLabel)
        self.tabWidget.addTab(self.trackinTab, "")
        self.loadCamTab = QtWidgets.QWidget()
        self.loadCamTab.setObjectName("loadCamTab")
        self.camBoxLabel = QtWidgets.QLabel(self.loadCamTab)
        self.camBoxLabel.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.camBoxLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.camBoxLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.camBoxLabel.setObjectName("camBoxLabel")
        self.openCamButton = QtWidgets.QPushButton(self.loadCamTab)
        self.openCamButton.setGeometry(QtCore.QRect(400, 220, 211, 171))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.openCamButton.setFont(font)
        self.openCamButton.setObjectName("openCamButton")
        self.tabWidget.addTab(self.loadCamTab, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1311, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuSettings = QtWidgets.QMenu(self.menubar)
        self.menuSettings.setObjectName("menuSettings")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew_Local_Tracking = QtWidgets.QAction(MainWindow)
        self.actionNew_Local_Tracking.setObjectName("actionNew_Local_Tracking")
        self.actionNew_Live_Tracking = QtWidgets.QAction(MainWindow)
        self.actionNew_Live_Tracking.setObjectName("actionNew_Live_Tracking")
        self.menuFile.addAction(self.actionNew_Local_Tracking)
        self.menuFile.addAction(self.actionNew_Live_Tracking)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Tracking Bot "))
        self.localModeButton.setText(_translate("MainWindow", "Local tracking"))
        self.liveModeButton.setText(_translate("MainWindow", "Live Tracking"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.menuTab), _translate("MainWindow", "Menu"))
        self.VBoxLabel.setText(_translate("MainWindow", "VBox"))
        self.loadVidButton.setText(_translate("MainWindow", "Load Video"))
        self.loadImgButton.setText(_translate("MainWindow", "Load Image"))
        self.vidPosLabel.setText(_translate("MainWindow", "mm:hh:ss"))
        self.vidLenLabel.setText(_translate("MainWindow", "mm:hh:ss"))
        self.vidNameLabel.setText(_translate("MainWindow", "File name"))
        self.vidDurLabel.setText(_translate("MainWindow", "Video duration (hh:mm:ss)"))
        self.vidFpsLabel.setText(_translate("MainWindow", "Frame rate (fps)"))
        self.vidResLabel.setText(_translate("MainWindow", "Resolution"))
        self.loadNewVidButton.setText(_translate("MainWindow", "New file"))
        self.caliTabLinkButton.setText(_translate("MainWindow", "Calibration"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.loadVidTab), _translate("MainWindow", "Load Video"))
        self.caliBoxLabel.setText(_translate("MainWindow", "Calibration"))
        self.caliUnitLabel.setText(_translate("MainWindow", "mm"))
        self.caliTabText1.setText(_translate("MainWindow", "Define actual scale"))
        self.drawScaleButton.setText(_translate("MainWindow", "Draw scale"))
        self.resetScaleButton.setText(_translate("MainWindow", "Reset"))
        self.applyScaleButton.setText(_translate("MainWindow", "Apply"))
        self.threTabLinkButton.setText(_translate("MainWindow", "Threshold"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.caliTab), _translate("MainWindow", "Calibration"))
        self.threBoxLabel.setText(_translate("MainWindow", "Threshold"))
        self.threTabText1.setText(_translate("MainWindow", "Number of objects"))
        self.threTabText2.setText(_translate("MainWindow", "Max"))
        self.threTabText3.setText(_translate("MainWindow", "Min"))
        self.threTabText4.setText(_translate("MainWindow", "Object size"))
        self.threTabText5.setText(_translate("MainWindow", "Block size"))
        self.threTabText6.setText(_translate("MainWindow", "Offset"))
        self.applyThreButton.setText(_translate("MainWindow", "Apply"))
        self.resetThreButton.setText(_translate("MainWindow", "Reset"))
        self.applyMaskcheckBox.setText(_translate("MainWindow", "Apply mask"))
        self.invertCtrcheckBox.setText(_translate("MainWindow", "Invert contrast"))
        self.threTabText7.setText(_translate("MainWindow", "Detection settings"))
        self.threPosLabel.setText(_translate("MainWindow", "mm:hh:ss"))
        self.threLenLabel.setText(_translate("MainWindow", "mm:hh:ss"))
        self.trackTabLinkButton.setText(_translate("MainWindow", "Tracking"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.threTab), _translate("MainWindow", "Threshold"))
        self.trackingeBoxLabel.setText(_translate("MainWindow", "Tracking"))
        self.trackPosLabel.setText(_translate("MainWindow", "mm:hh:ss"))
        self.trackLenLabel.setText(_translate("MainWindow", "mm:hh:ss"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.trackinTab), _translate("MainWindow", "Tracking"))
        self.camBoxLabel.setText(_translate("MainWindow", "CamBox"))
        self.openCamButton.setText(_translate("MainWindow", "Open Camera"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.loadCamTab), _translate("MainWindow", "Load Camera"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuSettings.setTitle(_translate("MainWindow", "Settings"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionNew_Local_Tracking.setText(_translate("MainWindow", "New Local Tracking"))
        self.actionNew_Live_Tracking.setText(_translate("MainWindow", "New Live Tracking"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
