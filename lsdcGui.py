#!/opt/conda_envs/lsdc_dev/bin/python
#####!/usr/bin/python
import sys
import os
import string
import math
import urllib
import cStringIO
from epics import PV


from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import * 
from PyQt4.QtGui import * 
import db_lib
from QtEpicsMotorEntry import *
from QtEpicsMotorLabel import *
from QtEpicsPVLabel import *
from QtEpicsPVEntry import *
import cv2
from cv2 import *
from PIL import Image
import ImageQt
import daq_utils
import albulaUtils
from testSimpleConsole import *
import functools
from QPeriodicTable import *
from PyMca.QtBlissGraph import QtBlissGraph
from PyMca.McaAdvancedFit import McaAdvancedFit
from PyMca import ElementsInfo
from element_info import element_info #skinner - this is what I used at NSLS-I
import numpy as np
import thread
import lsdcOlog
import StringIO

global sampleNameDict
sampleNameDict = {}

global containerDict
containerDict = {}




class snapCommentDialog(QDialog):
    def __init__(self,parent = None):
        QDialog.__init__(self,parent)
        self.setWindowTitle("Snapshot Comment")
        self.setModal(True)
        vBoxColParams1 = QtGui.QVBoxLayout()
        hBoxColParams1 = QtGui.QHBoxLayout()
        self.textEdit = QtGui.QPlainTextEdit()
        vBoxColParams1.addWidget(self.textEdit)
        self.ologCheckBox = QCheckBox("Save to Olog")
        self.ologCheckBox.setChecked(False)
        vBoxColParams1.addWidget(self.ologCheckBox)        
        commentButton = QtGui.QPushButton("Add Comment")        
        commentButton.clicked.connect(self.commentCB)
        cancelButton = QtGui.QPushButton("Cancel")        
        cancelButton.clicked.connect(self.cancelCB)
        
        hBoxColParams1.addWidget(commentButton)
        hBoxColParams1.addWidget(cancelButton)
        vBoxColParams1.addLayout(hBoxColParams1)
        self.setLayout(vBoxColParams1)

      
    def cancelCB(self):
      self.comment = ""
      self.useOlog = False
      self.reject()

    def commentCB(self):
      self.comment = self.textEdit.toPlainText()
      self.useOlog = self.ologCheckBox.isChecked()
      self.accept()
    
    @staticmethod
    def getComment(parent = None):
        dialog = snapCommentDialog(parent)
        result = dialog.exec_()
        return (dialog.comment, dialog.useOlog,result == QDialog.Accepted)

class rasterExploreDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setModal(False)
        self.setWindowTitle("Raster Explore")
        vBoxParams1 = QtGui.QVBoxLayout()
        hBoxParams1 = QtGui.QHBoxLayout()
        hBoxParams2 = QtGui.QHBoxLayout()
        hBoxParams3 = QtGui.QHBoxLayout()
        spotCountLabel = QtGui.QLabel('Spot Count:')
        spotCountLabel.setFixedWidth(120)
        self.spotCount_ledit = QtGui.QLabel()
        self.spotCount_ledit.setFixedWidth(60)
        hBoxParams1.addWidget(spotCountLabel)
        hBoxParams1.addWidget(self.spotCount_ledit)
        intensityLabel = QtGui.QLabel('Total Intensity:')
        intensityLabel.setFixedWidth(120)
        self.intensity_ledit = QtGui.QLabel()
        self.intensity_ledit.setFixedWidth(60)
        hBoxParams2.addWidget(intensityLabel)
        hBoxParams2.addWidget(self.intensity_ledit)
        resoLabel = QtGui.QLabel('Resolution:')
        resoLabel.setFixedWidth(120)
        self.reso_ledit = QtGui.QLabel()
        self.reso_ledit.setFixedWidth(60)
        hBoxParams3.addWidget(resoLabel)
        hBoxParams3.addWidget(self.reso_ledit)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.buttons()[0].clicked.connect(self.rasterExploreCancelCB)
        vBoxParams1.addLayout(hBoxParams1)
        vBoxParams1.addLayout(hBoxParams2)
        vBoxParams1.addLayout(hBoxParams3)
        vBoxParams1.addWidget(self.buttons)
        self.setLayout(vBoxParams1)


    def setSpotCount(self,val):
      self.spotCount_ledit.setText(str(val))

    def setTotalIntensity(self,val):
      self.intensity_ledit.setText(str(val))

    def setResolution(self,val):
      self.reso_ledit.setText(str(val))

    def rasterExploreCancelCB(self):
      self.done(QDialog.Rejected)


class screenDefaultsDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setModal(False)
        self.setWindowTitle("Raster Params")        
        vBoxColParams1 = QtGui.QVBoxLayout()
        hBoxColParams2 = QtGui.QHBoxLayout()
        colRangeLabel = QtGui.QLabel('Oscillation Width:')
        colRangeLabel.setFixedWidth(120)
        colRangeLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.osc_range_ledit = QtGui.QLineEdit()
        self.osc_range_ledit.setFixedWidth(60)
        self.osc_range_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultWidth")))
        colExptimeLabel = QtGui.QLabel('ExposureTime:')
        colExptimeLabel.setFixedWidth(120)
        colExptimeLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.exp_time_ledit = QtGui.QLineEdit()
        self.exp_time_ledit.setFixedWidth(60)
        self.exp_time_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTime")))
        hBoxColParams2.addWidget(colRangeLabel)
        hBoxColParams2.addWidget(self.osc_range_ledit)
        hBoxColParams2.addWidget(colExptimeLabel)
        hBoxColParams2.addWidget(self.exp_time_ledit)
        self.hBoxRasterLayout2 = QtGui.QHBoxLayout()
        rasterTuneLabel = QtGui.QLabel('Raster\nTuning')
        self.rasterResoCheckBox = QCheckBox("Constrain Resolution")
        if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneResoFlag") == 1):
          resoFlag = True
        else:
          resoFlag = False            
        self.rasterResoCheckBox.setChecked(resoFlag)
        
        self.rasterResoCheckBox.stateChanged.connect(self.rasterResoCheckCB)

        

        rasterLowResLabel  = QtGui.QLabel('LowRes:')
        self.rasterLowRes = QtGui.QLineEdit()
        self.rasterLowRes.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneLowRes")))
        self.rasterLowRes.setEnabled(False)
        rasterHighResLabel  = QtGui.QLabel('HighRes:')
        self.rasterHighRes = QtGui.QLineEdit()
        self.rasterHighRes.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneHighRes")))
        self.rasterHighRes.setEnabled(False)        
        self.rasterIceRingCheckBox = QCheckBox("Ice Ring")
        self.rasterIceRingCheckBox.setChecked(False)
        self.rasterIceRingCheckBox.stateChanged.connect(self.rasterIceRingCheckCB)        
        self.rasterIceRingWidth = QtGui.QLineEdit()
        self.rasterIceRingWidth.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingWidth")))
        self.rasterIceRingWidth.setEnabled(False)
        if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingFlag") == 1):
          iceRingFlag = True
        else:
          iceRingFlag = False            
        self.rasterIceRingCheckBox.setChecked(iceRingFlag)
#        self.hBoxRasterLayout2.addWidget(rasterTuneLabel)
        self.hBoxRasterLayout2.addWidget(self.rasterResoCheckBox)
        self.hBoxRasterLayout2.addWidget(rasterLowResLabel)
        self.hBoxRasterLayout2.addWidget(self.rasterLowRes)
        self.hBoxRasterLayout2.addWidget(rasterHighResLabel)
        self.hBoxRasterLayout2.addWidget(self.rasterHighRes)
        self.hBoxRasterLayout2.addWidget(self.rasterIceRingCheckBox)
        self.hBoxRasterLayout2.addWidget(self.rasterIceRingWidth)        


        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.buttons()[1].clicked.connect(self.screenDefaultsOKCB)
        self.buttons.buttons()[0].clicked.connect(self.screenDefaultsCancelCB)

#        vBoxColParams1.addLayout(hBoxColParams2)
        vBoxColParams1.addLayout(self.hBoxRasterLayout2)
        vBoxColParams1.addWidget(self.buttons)
#        vBoxColParams1.addWidget(cancelButton)
        self.setLayout(vBoxColParams1)

    def screenDefaultsCancelCB(self):
      self.done(QDialog.Rejected)

    def screenDefaultsOKCB(self):
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterDefaultWidth",float(self.osc_range_ledit.text()))
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTime",float(self.exp_time_ledit.text()))
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneLowRes",float(self.rasterLowRes.text()))
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneHighRes",float(self.rasterHighRes.text()))
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingWidth",float(self.rasterIceRingWidth.text()))
      if (self.rasterIceRingCheckBox.isChecked()):
        db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingFlag",1)
      else:
        db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneIceRingFlag",0)          
      if (self.rasterResoCheckBox.isChecked()):
        db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneResoFlag",1)
      else:
        db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterTuneResoFlag",0)          
      self.done(QDialog.Accepted)
    
    def rasterIceRingCheckCB(self,state):
      if state == QtCore.Qt.Checked:
        self.rasterIceRingWidth.setEnabled(True)        
      else:
        self.rasterIceRingWidth.setEnabled(False)          

    def rasterResoCheckCB(self,state):
      if state == QtCore.Qt.Checked:
        self.rasterLowRes.setEnabled(True)
        self.rasterHighRes.setEnabled(True)                
      else:
        self.rasterLowRes.setEnabled(False)
        self.rasterHighRes.setEnabled(False)                



class PuckDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        super(PuckDialog, self).__init__(parent)
        self.initData()
        self.initUI()


    def initData(self):
        puckListUnsorted = db_lib.getAllPucks(daq_utils.owner)
        puckList = sorted(puckListUnsorted,key=lambda i: i['time'],reverse=True)
        dewarObj = db_lib.getPrimaryDewar(daq_utils.beamline)
        pucksInDewar = dewarObj['content']

        data = []
#if you have to, you could store the puck_id in the item data
        for i in xrange(len(puckList)):
          if (puckList[i]["uid"] not in pucksInDewar):
            data.append(puckList[i]["name"])
        self.model = QtGui.QStandardItemModel()
        labels = QtCore.QStringList(("Name"))
        self.model.setHorizontalHeaderLabels(labels)
        for i in xrange(len(data)):
            name = QtGui.QStandardItem(data[i])
            self.model.appendRow(name)


    def initUI(self):
        self.tv = QtGui.QListView(self)
        self.tv.setModel(self.model)
        QtCore.QObject.connect(self.tv, QtCore.SIGNAL("doubleClicked (QModelIndex)"),self.containerOKCB)
        behavior = QtGui.QAbstractItemView.SelectRows
        self.tv.setSelectionBehavior(behavior)
        
        self.label = QtGui.QLabel(self)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.buttons()[0].clicked.connect(self.containerOKCB)
        self.buttons.buttons()[1].clicked.connect(self.containerCancelCB)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tv) 
        layout.addWidget(self.label)
        layout.addWidget(self.buttons)
        self.setLayout(layout)        
        self.tv.clicked.connect(self.onClicked)
            
    def containerOKCB(self):
      selmod = self.tv.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      if (indexes != []):
        i = 0
        item = self.model.itemFromIndex(indexes[i])
        text = str(item.text())
        self.label.setText(text)      
        self.accept()
        self.puckName = text
      else:
        text = ""
        self.reject()
        self.puckName = text
      

    def containerCancelCB(self):
      text = ""
      self.reject()
      self.puckName = text

        
    def onClicked(self, idx):
      item = self.model.itemFromIndex(idx)        
      text = str(item.text())

    @staticmethod
    def getPuckName(parent = None):
        dialog = PuckDialog(parent)
        result = dialog.exec_()
        return (dialog.puckName, result == QDialog.Accepted)



class DewarDialog(QtGui.QDialog):
    def __init__(self, parent = None,action="add"):
        super(DewarDialog, self).__init__(parent)
        self.pucksPerDewarSector = 3
        self.dewarSectors = 8
        self.action = action
        self.parent=parent

        self.initData()
        self.initUI()

    def initData(self):
      dewarObj = db_lib.getPrimaryDewar(daq_utils.beamline)
      puckLocs = dewarObj['content']
      self.data = []
      for i in xrange(len(puckLocs)):
#      for i in range(0,len(puckLocs)):          
        if (puckLocs[i] != ""):
          owner = db_lib.getContainerByID(puckLocs[i])["owner"]
          if (1):
#          if (owner == daq_utils.owner or daq_utils.owner == "skinner"):                            
            self.data.append(db_lib.getContainerNameByID(puckLocs[i]))
          else:
            self.data.append("private")
        else:
          self.data.append("Empty")
      print(self.data)


    def initUI(self):
        layout = QtGui.QVBoxLayout()
        headerLabelLayout = QtGui.QHBoxLayout()
        aLabel = QtGui.QLabel("A")
        aLabel.setFixedWidth(15)
        headerLabelLayout.addWidget(aLabel)
        bLabel = QtGui.QLabel("B")
        bLabel.setFixedWidth(10)
        headerLabelLayout.addWidget(bLabel)
        cLabel = QtGui.QLabel("C")
        cLabel.setFixedWidth(10)
        headerLabelLayout.addWidget(cLabel)
        layout.addLayout(headerLabelLayout)
        self.allButtonList = [None]*(self.dewarSectors*self.pucksPerDewarSector)
        for i in range (0,self.dewarSectors):
          rowLayout = QtGui.QHBoxLayout()
          numLabel = QtGui.QLabel(str(i+1))
          rowLayout.addWidget(numLabel)

          for j in range (0,self.pucksPerDewarSector):
            dataIndex = (i*self.pucksPerDewarSector)+j            
#            print dataIndex
            self.allButtonList[dataIndex] = QtGui.QPushButton((str(self.data[dataIndex])))
#            self.allButtonList[dataIndex] = self.buttons.addButton(str(self.data[dataIndex]),0)            
            self.allButtonList[dataIndex].clicked.connect(functools.partial(self.on_button,str(dataIndex)))
            rowLayout.addWidget(self.allButtonList[dataIndex])
          layout.addLayout(rowLayout)
        cancelButton = QtGui.QPushButton("Done")        
        cancelButton.clicked.connect(self.containerCancelCB)
        layout.addWidget(cancelButton)
        self.setLayout(layout)        
            
    def on_button(self, n):
      if (self.action == "remove"):
        self.dewarPos = n
#        print "delete puck " + str(n)
        db_lib.removePuckFromDewar(daq_utils.beamline,int(n))
        self.allButtonList[int(n)].setText("Empty")
        self.parent.treeChanged_pv.put(1)
      else:
        self.dewarPos = n
        self.accept()


    def containerCancelCB(self):
      self.dewarPos = 0
      self.reject()

    @staticmethod
    def getDewarPos(parent = None,action="add"):
        dialog = DewarDialog(parent,action)
        result = dialog.exec_()
        return (dialog.dewarPos, result == QDialog.Accepted)


class DewarTree(QtGui.QTreeView):
    def __init__(self, parent=None):
        super(DewarTree, self).__init__(parent)
        self.pucksPerDewarSector = 3
        self.dewarSectors = 8
        self.parent=parent
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.setAnimated(True)
        self.model = QtGui.QStandardItemModel()
        self.model.itemChanged.connect(self.queueSelectedSample)
        self.isExpanded = 1

    def keyPressEvent(self, event):
      if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace):
#        print "caught the delete key"
        self.deleteSelectedCB(0)
      else:
        super(DewarTree,self).keyPressEvent(event)  

    def refreshTree(self):
      self.parent.dewarViewToggleCheckCB()

    def refreshTreeDewarView(self):
        startTime = time.time()
        selectedIndex = None
        mountedIndex = None
        selectedSampleIndex = None
        puck = ""
        collectionRunning = False
        self.model.clear()
        st = time.time()
        dewarContents = db_lib.getContainerByName(daq_utils.primaryDewarName,daq_utils.beamline)['content']
#        print("getContainerByName " + str(time.time() - st))
        for i in range (0,len(dewarContents)): #dewar contents is the list of puck IDs
          parentItem = self.model.invisibleRootItem()
          if (dewarContents[i]==""):
            puck = ""
            puckName = ""
          else:
            st = time.time()
            if (dewarContents[i] not in containerDict):
              puck = db_lib.getContainerByID(dewarContents[i])
              containerDict[dewarContents[i]] = puck
            else:
              puck = containerDict[dewarContents[i]]
#            print("getContainerByID " + str(time.time() - st))
            if (1):
#            if (puck["owner"] == daq_utils.owner or daq_utils.owner == "skinner"):                
              puckName = puck["name"]
            else:
              puckName = "private"
          index_s = "%d%s" % ((i)/self.pucksPerDewarSector+1,chr(((i)%self.pucksPerDewarSector)+ord('A')))
          item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), QtCore.QString(index_s + " " + puckName))
          item.setData(puckName,32)
          item.setData("container",33)          
          parentItem.appendRow(item)
          parentItem = item
          if (puck != "" and puckName != "private"):
            puckContents = puck['content']
            puckSize = len(puckContents)
            for j in range (0,len(puckContents)):#should be the list of samples
              if (puckContents[j] != ""):
                st = time.time()
                if (puckContents[j] not in sampleNameDict):
                  sampleName = db_lib.getSampleNamebyID(puckContents[j])
                  sampleNameDict[puckContents[j]] = sampleName
                else:
                  sampleName = sampleNameDict[puckContents[j]]
                position_s = str(j+1) + "-" + sampleName
#                print("getSampNameByID " + str(time.time() - st))
                item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), QtCore.QString(position_s))
                item.setData(puckContents[j],32) #just stuck sampleID there, but negate it to diff from reqID
                item.setData("sample",33)
                if (puckContents[j] == self.parent.mountedPin_pv.get()):
                  item.setForeground(QtGui.QColor('red'))       
                  font = QtGui.QFont()
                  font.setItalic(True)
                  font.setOverline(True)
                  font.setUnderline(True)
                  item.setFont(font)
                parentItem.appendRow(item)
                if (puckContents[j] == self.parent.mountedPin_pv.get()):
                  mountedIndex = self.model.indexFromItem(item)
                if (puckContents[j] == self.parent.selectedSampleID): #looking for the selected item
                  print "found " + str(self.parent.SelectedItemData)
                  selectedSampleIndex = self.model.indexFromItem(item)
                st = time.time()
                sampleRequestList = db_lib.getRequestsBySampleID(puckContents[j])
#                print("getReqsBySampID " + str(time.time() - st))
                for k in xrange(len(sampleRequestList)):
                  if not (sampleRequestList[k]["request_obj"].has_key("protocol")):
                    continue
                  col_item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), QtCore.QString(sampleRequestList[k]["request_obj"]["file_prefix"]+"_"+sampleRequestList[k]["request_obj"]["protocol"]))
                  col_item.setData(sampleRequestList[k]["uid"],32)
                  col_item.setData("request",33)                  
                  col_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
                  if (sampleRequestList[k]["priority"] == 99999):
                    col_item.setCheckState(Qt.Checked)
                    col_item.setBackground(QtGui.QColor('green'))
                    selectedIndex = self.model.indexFromItem(col_item) ##attempt to leave it on the request after collection
                    
                    collectionRunning = True
                    self.parent.refreshCollectionParams(sampleRequestList[k])
#did nothing                    self.setCurrentIndex(selectedIndex)
                  elif (sampleRequestList[k]["priority"] > 0):
                    col_item.setCheckState(Qt.Checked)
                    col_item.setBackground(QtGui.QColor('white'))
                  elif (sampleRequestList[k]["priority"]< 0):
#                    col_item.setCheckState(Qt.Unchecked)
                    col_item.setCheckable(False)
                    col_item.setBackground(QtGui.QColor('cyan'))
                  else:
                    col_item.setCheckState(Qt.Unchecked)
                    col_item.setBackground(QtGui.QColor('white'))
                  item.appendRow(col_item)
                  if (sampleRequestList[k]["uid"] == self.parent.SelectedItemData): #looking for the selected item, this is a request
#                    print("found the selected sample from request")
                    selectedIndex = self.model.indexFromItem(col_item)
              else : #this is an empty spot, no sample
                position_s = str(j+1)
                item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), QtCore.QString(position_s))
                item.setData("",32)
##                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
##                item.setCheckState(Qt.Unchecked)
                parentItem.appendRow(item)

        self.setModel(self.model)
        if (selectedSampleIndex != None and collectionRunning == False):
#          print "selectedSampleIndex = " + str(selectedSampleIndex)
          self.setCurrentIndex(selectedSampleIndex)
          if (mountedIndex != None):
            self.model.itemFromIndex(mountedIndex).setForeground(QtGui.QColor('red'))       
            font = QtGui.QFont()
            font.setUnderline(True)
            font.setItalic(True)
            font.setOverline(True)
            self.model.itemFromIndex(mountedIndex).setFont(font)
          self.parent.row_clicked(selectedSampleIndex)
        elif (selectedSampleIndex == None and collectionRunning == False):
          if (mountedIndex != None):
            self.setCurrentIndex(mountedIndex)
            self.model.itemFromIndex(mountedIndex).setForeground(QtGui.QColor('red'))       
            font = QtGui.QFont()
            font.setUnderline(True)
            font.setItalic(True)
            font.setOverline(True)
            self.model.itemFromIndex(mountedIndex).setFont(font)
            self.parent.row_clicked(mountedIndex)
        else:
          pass
        if (selectedIndex != None and collectionRunning == False):
          self.setCurrentIndex(selectedIndex)
          self.parent.row_clicked(selectedIndex)
        if (collectionRunning == True):
          if (mountedIndex != None):
            self.setCurrentIndex(mountedIndex)
#            if (selectedIndex != None):
#              self.setCurrentIndex(selectedIndex)            
##            self.parent.row_clicked(mountedIndex)

        if (self.isExpanded):
          self.expandAll()
        else:
          self.collapseAll()
        self.scrollTo(self.currentIndex(),QAbstractItemView.PositionAtCenter)
        print("refresh time = " + str(time.time()-startTime))


    def refreshTreePriorityView(self): #"item" is a sample, "col_items" are requests which are children of samples.
        collectionRunning = False
        selectedIndex = None
        mountedIndex = None
        selectedSampleIndex = None
        self.model.clear()
        self.orderedRequests = db_lib.getOrderedRequestList(daq_utils.beamline)
        dewarContents = db_lib.getContainerByName(daq_utils.primaryDewarName,daq_utils.beamline)['content']
        maxPucks = len(dewarContents)
        requestedSampleList = []
        mountedPin = self.parent.mountedPin_pv.get()
        for i in xrange(len(self.orderedRequests)): # I need a list of samples for parent nodes
          if (self.orderedRequests[i]["sample"] not in requestedSampleList):
            requestedSampleList.append(self.orderedRequests[i]["sample"])
        for i in xrange(len(requestedSampleList)):
          sample = db_lib.getSampleByID(requestedSampleList[i])
          owner = sample["owner"]
          parentItem = self.model.invisibleRootItem()
#          (puckPosition,samplePositionInContainer,containerID) = db_lib.getCoordsfromSampleID(requestedSampleList[i])
#          containerName = db_lib.getContainerNameByID(containerID)
#          index_s = "%d%s" % ((puckPosition)/self.pucksPerDewarSector+1,chr(((puckPosition)%self.pucksPerDewarSector)+ord('A')))
          if (1):
#          if (owner == daq_utils.owner):              
            nodeString = QtCore.QString(str(db_lib.getSampleNamebyID(requestedSampleList[i])))
          else:
            nodeString = QtCore.QString("private")
          item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), nodeString)
          item.setData(requestedSampleList[i],32)
          item.setData("sample",33)          
          if (requestedSampleList[i] == mountedPin):
            item.setForeground(QtGui.QColor('red'))       
            font = QtGui.QFont()
            font.setItalic(True)
            font.setOverline(True)
            font.setUnderline(True)
            item.setFont(font)
          parentItem.appendRow(item)
          if (requestedSampleList[i] == mountedPin):
            mountedIndex = self.model.indexFromItem(item)
          if (requestedSampleList[i] == self.parent.selectedSampleID): #looking for the selected item
            selectedSampleIndex = self.model.indexFromItem(item)
          parentItem = item
          for k in xrange(len(self.orderedRequests)):
            if (self.orderedRequests[k]["sample"] == requestedSampleList[i]):
              if (1):
#              if (owner == daq_utils.owner):                  
                col_item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), QtCore.QString(self.orderedRequests[k]["request_obj"]["file_prefix"]+"_"+self.orderedRequests[k]["request_obj"]["protocol"]))
              else:
                col_item = QtGui.QStandardItem(QtGui.QIcon(":/trolltech/styles/commonstyle/images/file-16.png"), QtCore.QString("private"))
              col_item.setData(self.orderedRequests[k]["uid"],32)
              col_item.setData("request",33)                  
              col_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
              if (self.orderedRequests[k]["priority"] == 99999):
                col_item.setCheckState(Qt.Checked)
                col_item.setBackground(QtGui.QColor('green'))
                collectionRunning = True
                self.parent.refreshCollectionParams(self.orderedRequests[k])

              elif (self.orderedRequests[k]["priority"] > 0):
                col_item.setCheckState(Qt.Checked)
                col_item.setBackground(QtGui.QColor('white'))
              elif (self.orderedRequests[k]["priority"]< 0):
#                col_item.setCheckState(Qt.Unchecked)
                col_item.setCheckable(False)                
                col_item.setBackground(QtGui.QColor('cyan'))
              else:
                col_item.setCheckState(Qt.Unchecked)
                col_item.setBackground(QtGui.QColor('white'))
              item.appendRow(col_item)
              if (self.orderedRequests[k]["uid"] == self.parent.SelectedItemData): #looking for the selected item
                selectedIndex = self.model.indexFromItem(col_item)
        self.setModel(self.model)
        if (selectedSampleIndex != None and collectionRunning == False):
          self.setCurrentIndex(selectedSampleIndex)
          self.parent.row_clicked(selectedSampleIndex)
        elif (selectedSampleIndex == None and collectionRunning == False):
          if (mountedIndex != None):
            self.setCurrentIndex(mountedIndex)
            self.parent.row_clicked(mountedIndex)
        else:
          pass

        if (selectedIndex != None and collectionRunning == False):
          self.setCurrentIndex(selectedIndex)
          self.parent.row_clicked(selectedIndex)
        self.scrollTo(self.currentIndex(),QAbstractItemView.PositionAtCenter)
        self.expandAll()


    def queueSelectedSample(self,item):
#        print "queueing selected sample"
        reqID = str(item.data(32).toString())
        checkedSampleRequest = db_lib.getRequestByID(reqID) #line not needed???
        if (item.checkState() == Qt.Checked):
          db_lib.updatePriority(reqID,5000)
        else:
          db_lib.updatePriority(reqID,0)
        item.setBackground(QtGui.QColor('white'))
#        self.parent.treeChanged_pv.put(1) #not sure why I don't just call the update routine, although this allows multiple guis
        self.parent.treeChanged_pv.put(self.parent.processID) #the idea is touch the pv, but have this gui instance not refresh
#        self.refreshTree()        

    def queueAllSelectedCB(self):
      selmod = self.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      for i in xrange(len(indexes)):
        item = self.model.itemFromIndex(indexes[i])
        itemData = str(item.data(32).toString())
        itemDataType = str(item.data(33).toString())
        if (itemDataType == "request"): 
          selectedSampleRequest = db_lib.getRequestByID(itemData)
          db_lib.updatePriority(itemData,5000)
#      self.refreshTree()
      self.parent.treeChanged_pv.put(1)


    def deQueueAllSelectedCB(self):
      selmod = self.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      for i in xrange(len(indexes)):
        item = self.model.itemFromIndex(indexes[i])
        itemData = str(item.data(32).toString())
        itemDataType = str(item.data(33).toString())
        if (itemDataType == "request"): 
          selectedSampleRequest = db_lib.getRequestByID(itemData)
          db_lib.updatePriority(itemData,0)
      self.parent.treeChanged_pv.put(1)

    def deleteSelectedCB(self,deleteAll):
      if (deleteAll):
        self.selectAll()            
      selmod = self.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      progressInc = 100.0/float(len(indexes))
      self.parent.progressDialog.setWindowTitle("Deleting Requests")
      self.parent.progressDialog.show()
      for i in xrange(len(indexes)):
        self.parent.progressDialog.setValue(int((i+1)*progressInc))
        item = self.model.itemFromIndex(indexes[i])
        itemData = str(item.data(32).toString())
        itemDataType = str(item.data(33).toString())
        if (itemDataType == "request"): 
          selectedSampleRequest = db_lib.getRequestByID(itemData)
          self.selectedSampleID = selectedSampleRequest["sample"]
          db_lib.deleteRequest(selectedSampleRequest["uid"])
          if (selectedSampleRequest["request_obj"]["protocol"] == "raster" or selectedSampleRequest["request_obj"]["protocol"] == "stepRaster"):
            for i in xrange(len(self.parent.rasterList)):
              if (self.parent.rasterList[i] != None):
                if (self.parent.rasterList[i]["uid"] == selectedSampleRequest["uid"]):
                  self.parent.scene.removeItem(self.parent.rasterList[i]["graphicsItem"])
                  self.parent.rasterList[i] = None
          if (selectedSampleRequest["request_obj"]["protocol"] == "vector" or selectedSampleRequest["request_obj"]["protocol"] == "stepVector"):
            self.parent.clearVectorCB()
      self.parent.progressDialog.close()
      self.parent.treeChanged_pv.put(1)
      

    def expandAllCB(self):
      self.expandAll()
      self.isExpanded = 1

    def collapseAllCB(self):
      self.collapseAll()
      self.isExpanded = 0



class DataLocInfo(QtGui.QGroupBox):

    def __init__(self,parent=None):
        QGroupBox.__init__(self,parent)
        self.parent = parent
#        self.dataPathGB = QtGui.QGroupBox()
        self.setTitle("Data Location")
        self.vBoxDPathParams1 = QtGui.QVBoxLayout()
        self.hBoxDPathParams1 = QtGui.QHBoxLayout()
        self.basePathLabel = QtGui.QLabel('Base Path:')
        self.base_path_ledit = QtGui.QLineEdit() #leave editable for now
        self.base_path_ledit.setText(os.getcwd())
        self.base_path_ledit.textChanged[str].connect(self.basePathTextChanged)
        self.browseBasePathButton = QtGui.QPushButton("Browse...") 
        self.browseBasePathButton.clicked.connect(self.parent.popBaseDirectoryDialogCB)
        self.hBoxDPathParams1.addWidget(self.basePathLabel)
        self.hBoxDPathParams1.addWidget(self.base_path_ledit)
        self.hBoxDPathParams1.addWidget(self.browseBasePathButton)
        self.hBoxDPathParams2 = QtGui.QHBoxLayout()
        self.dataPrefixLabel = QtGui.QLabel('Data Prefix:\n(40 Char Limit)')
        self.prefix_ledit = QtGui.QLineEdit()
        self.prefix_ledit.textChanged[str].connect(self.prefixTextChanged)
        self.hBoxDPathParams2.addWidget(self.dataPrefixLabel)
        self.hBoxDPathParams2.addWidget(self.prefix_ledit)
        self.dataNumstartLabel = QtGui.QLabel('File Number Start:')
        self.file_numstart_ledit = QtGui.QLineEdit()
        self.file_numstart_ledit.setFixedWidth(50)
        self.hBoxDPathParams3 = QtGui.QHBoxLayout()
        self.dataPathLabel = QtGui.QLabel('Data Path:')
        self.dataPath_ledit = QtGui.QLineEdit()
        self.dataPath_ledit.setFrame(False)
#        self.dataPath_ledit = QtGui.QLabel()        
        self.dataPath_ledit.setReadOnly(True)
        self.hBoxDPathParams3.addWidget(self.dataPathLabel)
        self.hBoxDPathParams3.addWidget(self.dataPath_ledit)
        self.hBoxDPathParams2.addWidget(self.dataNumstartLabel)
        self.hBoxDPathParams2.addWidget(self.file_numstart_ledit)
        self.vBoxDPathParams1.addLayout(self.hBoxDPathParams1)
        self.vBoxDPathParams1.addLayout(self.hBoxDPathParams2)
        self.vBoxDPathParams1.addLayout(self.hBoxDPathParams3)
        self.setLayout(self.vBoxDPathParams1)


    def basePathTextChanged(self,text):
      prefix = self.prefix_ledit.text()
#      runNum = db_lib.getSampleRequestCount(self.selectedSampleID)
      self.setDataPath_ledit(text+"/" + str(daq_utils.getVisitName()) + "/"+prefix+"/#/")
#      self.setDataPath_ledit(text+"/" + str(daq_utils.getProposalID()) + "/"+prefix+"/#/")            

    def prefixTextChanged(self,text):
      prefix = self.prefix_ledit.text()
      runNum = db_lib.getSampleRequestCount(self.parent.selectedSampleID)
      (puckPosition,samplePositionInContainer,containerID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,self.parent.selectedSampleID)
      self.setDataPath_ledit(self.base_path_ledit.text()+"/"+ str(daq_utils.getVisitName()) + "/"+prefix+"/"+str(runNum+1)+"/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/")      
#      self.setDataPath_ledit(self.base_path_ledit.text()+"/"+ str(daq_utils.getProposalID()) + "/"+prefix+"/"+str(runNum+1)+"/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/")      
      

    def setFileNumstart_ledit(self,s):
      self.file_numstart_ledit.setText(s)

    def setFilePrefix_ledit(self,s):
      self.prefix_ledit.setText(s)

    def setBasePath_ledit(self,s):
      self.base_path_ledit.setText(s)

    def setDataPath_ledit(self,s):
      self.dataPath_ledit.setText(s)



class rasterCell(QtGui.QGraphicsRectItem):

    def __init__(self,x,y,w,h,topParent,scene):
      super(rasterCell,self).__init__(x,y,w,h,None,scene)
      self.topParent = topParent
      self.setAcceptHoverEvents(True)

    def mousePressEvent(self, e):
      if (self.topParent.vidActionRasterExploreRadio.isChecked()):
        if (self.data(0) != None):
          spotcount = self.data(0).toInt()[0]
          filename = self.data(1).toString()
          d_min = self.data(2).toDouble()[0]
          intensity = self.data(3).toInt()[0]
          if (self.topParent.albulaDispCheckBox.isChecked()):
            if (str(self.data(1).toString()) != "empty"):
#              albulaUtils.albulaDispH5(str(self.data(1).toString()),self.data(2).toInt()[0])
              albulaUtils.albulaDispFile(str(self.data(1).toString()))
          if not (self.topParent.rasterExploreDialog.isVisible()):
            self.topParent.rasterExploreDialog.show()
          self.topParent.rasterExploreDialog.setSpotCount(spotcount)
          self.topParent.rasterExploreDialog.setTotalIntensity(intensity)
          self.topParent.rasterExploreDialog.setResolution(d_min)
          groupList = self.group().childItems()
          for i in range (0,len(groupList)):
            groupList[i].setPen(self.topParent.redPen)
          self.setPen(self.topParent.yellowPen)
                                              
      else:
        super(rasterCell, self).mousePressEvent(e)


    def hoverEnterEvent(self, e):
      if (1):
        if (self.data(0) != None):
          spotcount = self.data(0).toInt()[0]
#          filename = self.data(1).toString()
          d_min = self.data(2).toDouble()[0]
          intensity = self.data(3).toInt()[0]
          if not (self.topParent.rasterExploreDialog.isVisible()):
            self.topParent.rasterExploreDialog.show()
          self.topParent.rasterExploreDialog.setSpotCount(spotcount)
          self.topParent.rasterExploreDialog.setTotalIntensity(intensity)
          self.topParent.rasterExploreDialog.setResolution(d_min)
      else:
        super(rasterCell, self).hoverEnterEvent(e)



class rasterGroup(QtGui.QGraphicsItemGroup):
    def __init__(self,parent = None):
        super(rasterGroup, self).__init__()
        self.parent=parent
        self.setHandlesChildEvents(False)
#        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
#        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)


    def mousePressEvent(self, e):
      super(rasterGroup, self).mousePressEvent(e)
      print "mouse pressed on group"
#      self.setScale(-1.0)
      for i in xrange(len(self.parent.rasterList)):
        if (self.parent.rasterList[i] != None):
          if (self.parent.rasterList[i]["graphicsItem"].isSelected()):
            print "found selected raster"
            self.parent.SelectedItemData = self.parent.rasterList[i]["uid"]
            self.parent.treeChanged_pv.put(1)




    def mouseMoveEvent(self, e):

#        if e.buttons() != QtCore.Qt.RightButton:                      
#        QtGui.QWidget.mouseMoveEvent(self, e)   
        if e.buttons() == QtCore.Qt.LeftButton:
          pass
#            print 'left move'
        if e.buttons() == QtCore.Qt.RightButton:
          pass
#            print 'right move'

        super(rasterGroup, self).mouseMoveEvent(e)
        print "pos " + str(self.pos())
#        print "scene pos " + str(self.scenePos()

    def mouseReleaseEvent(self, e):
        super(rasterGroup, self).mouseReleaseEvent(e)
        if e.button() == QtCore.Qt.LeftButton:
          pass
#            print 'left release'
        if e.button() == QtCore.Qt.RightButton:
#            print 'right release'
          pass

#        print "released at " + str(self.pos())
#        print "released at scene pos " + str(self.scenePos())



class controlMain(QtGui.QMainWindow):
#1/13/15 - are these necessary?, 4/1 - still no idea
    Signal = QtCore.pyqtSignal()
    refreshTreeSignal = QtCore.pyqtSignal()
    serverMessageSignal = QtCore.pyqtSignal()
    serverPopupMessageSignal = QtCore.pyqtSignal()
    programStateSignal = QtCore.pyqtSignal()
    pauseButtonStateSignal = QtCore.pyqtSignal()    

    
    def __init__(self):
        super(controlMain, self).__init__()
        self.SelectedItemData = "" #attempt to know what row is selected
        self.popUpMessageInit = 1 # I hate these next two, but I don't want to catch old messages. Fix later, maybe.
        self.textWindowMessageInit = 1
        self.processID = os.getpid()
        self.popupMessage = QtGui.QErrorMessage(self)
        self.popupMessage.setStyleSheet("background-color: red")
        self.popupMessage.setModal(False)
        self.groupName = "skinner"
#        self.owner = "johns"
        self.vectorStart = None
        self.vectorEnd = None
        self.centerMarkerCharSize = 20
        self.centerMarkerCharOffsetX = 12
        self.centerMarkerCharOffsetY = 18
        self.currentRasterCellList = []
        self.redPen = QtGui.QPen(QtCore.Qt.red)
        self.bluePen = QtGui.QPen(QtCore.Qt.blue)
        self.yellowPen = QtGui.QPen(QtCore.Qt.yellow)                                
        self.initUI()
        self.lowMagCursorX_pv = PV(daq_utils.pvLookupDict["lowMagCursorX"])
        self.lowMagCursorY_pv = PV(daq_utils.pvLookupDict["lowMagCursorY"])
        self.highMagCursorX_pv = PV(daq_utils.pvLookupDict["highMagCursorX"])
        self.highMagCursorY_pv = PV(daq_utils.pvLookupDict["highMagCursorY"])
        self.fastShutterOpenPos_pv = PV(daq_utils.pvLookupDict["fastShutterOpenPos"])                
        self.rasterStepDefs = {"Coarse":30.0,"Fine":10.0,"VFine":5.0}
        self.createSampleTab()
        
        self.initCallbacks()
        self.motPos = {"x":self.sampx_pv.get(),"y":self.sampy_pv.get(),"z":self.sampz_pv.get(),"omega":self.omega_pv.get()}        
        self.dewarTree.refreshTreeDewarView()
        if (self.mountedPin_pv.get() == ""):
          mountedPin = db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample')["sampleID"]
          self.mountedPin_pv.put(mountedPin)
        self.rasterExploreDialog = rasterExploreDialog()
        self.detDistMotorEntry.getEntry().setText(self.detDistRBVLabel.getEntry().text()) #this is to fix the current val being overwritten by reso
        self.proposalID = -999999
        self.XRFInfoDict = self.parseXRFTable() #I don't like this
#        while (1):
        while (0):            
          proposalID=daq_utils.getProposalID()
          text, ok = QtGui.QInputDialog.getInteger(self, 'Input Dialog','Enter your 6-digit Proposal ID:',value=proposalID)
          if ok:
#            print(str(text))
            propID = int(text)
            if (propID != -999999): #assume they entered a real propID
              daq_utils.setProposalID(int(text))
              self.proposalID = propID              
              try:
                self.dataPathGB.prefixTextChanged("")
                self.EScanDataPathGBTool.prefixTextChanged("")
                self.EScanDataPathGB.prefixTextChanged("")
              except KeyError:
                pass
              break

    def parseXRFTable(self):
      XRFFile = open(os.environ["CONFIGDIR"] + "/XRF-AMX_simple.txt")
      XRFInfoDict = {}
      for line in XRFFile.readlines():
        tokens = line.split()
        XRFInfoDict[tokens[0]] = int(float(tokens[5])*100)
      XRFFile.close()
      return XRFInfoDict
        


    def closeEvent(self, evnt):
       evnt.accept()
       sys.exit() #doing this to close any windows left open

      
    def initVideo2(self,frequency):
#      self.captureZoom=cv2.VideoCapture("http://xf17id1c-ioc2.cs.nsls2.local:8008/C1.MJPG.mjpg")
      self.captureHighMag=cv2.VideoCapture(daq_utils.highMagCamURL)

    def initVideo4(self,frequency):
      self.captureHighMagZoom=cv2.VideoCapture(daq_utils.highMagZoomCamURL)
      

    def initVideo3(self,frequency):
      self.captureLowMagZoom=cv2.VideoCapture(daq_utils.lowMagZoomCamURL)

            
    def createSampleTab(self):

        sampleTab= QtGui.QWidget()      
        splitter1 = QtGui.QSplitter(Qt.Horizontal)
        vBoxlayout= QtGui.QVBoxLayout()
        self.dewarTreeFrame = QFrame()
        vBoxDFlayout= QtGui.QVBoxLayout()
        self.selectedSampleRequest = {}
        self.selectedSampleID = ""
        self.dewarTree   = DewarTree(self)
        QtCore.QObject.connect(self.dewarTree, QtCore.SIGNAL("clicked (QModelIndex)"),self.row_clicked)
        treeSelectBehavior = QtGui.QAbstractItemView.SelectItems
        treeSelectMode = QtGui.QAbstractItemView.ExtendedSelection
        self.dewarTree.setSelectionMode(treeSelectMode)
        self.dewarTree.setSelectionBehavior(treeSelectBehavior)
        hBoxRadioLayout1= QtGui.QHBoxLayout()   
        self.viewRadioGroup=QtGui.QButtonGroup()
        self.priorityViewRadio = QtGui.QRadioButton("PriorityView")
#        self.priorityViewRadio.setChecked(True)
        self.priorityViewRadio.toggled.connect(functools.partial(self.dewarViewToggledCB,"priorityView"))
        self.viewRadioGroup.addButton(self.priorityViewRadio)
        self.dewarViewRadio = QtGui.QRadioButton("DewarView")
        self.dewarViewRadio.setChecked(True)        
        self.dewarViewRadio.toggled.connect(functools.partial(self.dewarViewToggledCB,"dewarView"))
        hBoxRadioLayout1.addWidget(self.dewarViewRadio)        
        hBoxRadioLayout1.addWidget(self.priorityViewRadio)
        self.viewRadioGroup.addButton(self.dewarViewRadio)
        vBoxDFlayout.addLayout(hBoxRadioLayout1)
        vBoxDFlayout.addWidget(self.dewarTree)
        queueSelectedButton = QtGui.QPushButton("Queue All Selected")        
        queueSelectedButton.clicked.connect(self.dewarTree.queueAllSelectedCB)
        deQueueSelectedButton = QtGui.QPushButton("deQueue All Selected")        
        deQueueSelectedButton.clicked.connect(self.dewarTree.deQueueAllSelectedCB)
        runQueueButton = QtGui.QPushButton("Collect Queue")
        runQueueButton.setStyleSheet("background-color: yellow")
        runQueueButton.clicked.connect(self.collectQueueCB)
        stopRunButton = QtGui.QPushButton("Stop Collection")
        stopRunButton.setStyleSheet("background-color: red")
        stopRunButton.clicked.connect(self.stopRunCB) #immediate stop everything
#        stopRunButton.clicked.connect(self.stopQueueCB) #this stops before the next sample
        puckToDewarButton = QtGui.QPushButton("Puck to Dewar...")        
        mountSampleButton = QtGui.QPushButton("Mount Sample")        
        mountSampleButton.clicked.connect(self.mountSampleCB)
        unmountSampleButton = QtGui.QPushButton("Unmount Sample")        
        unmountSampleButton.clicked.connect(self.unmountSampleCB)
        puckToDewarButton.clicked.connect(self.puckToDewarCB)
        removePuckButton = QtGui.QPushButton("Remove Puck...")        
        removePuckButton.clicked.connect(self.removePuckCB)
        expandAllButton = QtGui.QPushButton("Expand All")        
        expandAllButton.clicked.connect(self.dewarTree.expandAllCB)
        collapseAllButton = QtGui.QPushButton("Collapse All")        
        collapseAllButton.clicked.connect(self.dewarTree.collapseAllCB)
        self.pauseQueueButton = QtGui.QPushButton("Pause")
        self.pauseQueueButton.clicked.connect(self.stopQueueCB) 
        emptyQueueButton = QtGui.QPushButton("Empty Queue")
        emptyQueueButton.clicked.connect(functools.partial(self.dewarTree.deleteSelectedCB,1))
        warmupButton = QtGui.QPushButton("Warmup Gripper")        
        warmupButton.clicked.connect(self.warmupGripperCB)
        
        

###        self.statusLabel = QtEpicsPVLabel(daq_utils.beamline+"_comm:program_state",self,300,highlight_on_change=False)
#        self.statusLabel = QtEpicsPVLabel(daq_utils.beamline+"_comm:program_state",self,300)
###        self.statusLabel.getEntry().setAlignment(QtCore.Qt.AlignCenter) 
        hBoxTreeButtsLayout = QtGui.QHBoxLayout()
        vBoxTreeButtsLayoutLeft = QtGui.QVBoxLayout()
        vBoxTreeButtsLayoutRight = QtGui.QVBoxLayout()
        vBoxTreeButtsLayoutLeft.addWidget(runQueueButton)
        vBoxTreeButtsLayoutLeft.addWidget(stopRunButton)
        vBoxTreeButtsLayoutLeft.addWidget(mountSampleButton)
        vBoxTreeButtsLayoutLeft.addWidget(self.pauseQueueButton)
        vBoxTreeButtsLayoutLeft.addWidget(expandAllButton)
        vBoxTreeButtsLayoutLeft.addWidget(unmountSampleButton)
        vBoxTreeButtsLayoutRight.addWidget(puckToDewarButton)
        vBoxTreeButtsLayoutRight.addWidget(removePuckButton)
        vBoxTreeButtsLayoutRight.addWidget(queueSelectedButton)
        vBoxTreeButtsLayoutRight.addWidget(deQueueSelectedButton)
        vBoxTreeButtsLayoutRight.addWidget(collapseAllButton)
        vBoxTreeButtsLayoutRight.addWidget(emptyQueueButton)
#        vBoxTreeButtsLayoutRight.addWidget(warmupButton)
        hBoxTreeButtsLayout.addLayout(vBoxTreeButtsLayoutLeft)
        hBoxTreeButtsLayout.addLayout(vBoxTreeButtsLayoutRight)
        vBoxDFlayout.addLayout(hBoxTreeButtsLayout)
        vBoxDFlayout.addWidget(warmupButton)        
###        vBoxDFlayout.addWidget(self.statusLabel.getEntry())
        self.dewarTreeFrame.setLayout(vBoxDFlayout)
        splitter1.addWidget(self.dewarTreeFrame)
        splitter11 = QtGui.QSplitter(Qt.Horizontal)
        self.mainSetupFrame = QFrame()
        self.mainSetupFrame.setFixedHeight(890)
        vBoxMainSetup = QtGui.QVBoxLayout()
        self.mainToolBox = QtGui.QToolBox()
#        self.mainToolBox.setFixedWidth(570)
        self.mainToolBox.setMinimumWidth(570)
        self.mainColFrame = QFrame()
        vBoxMainColLayout= QtGui.QVBoxLayout()
        colParamsGB = QtGui.QGroupBox()
        colParamsGB.setTitle("Acquisition")
        vBoxColParams1 = QtGui.QVBoxLayout()
        hBoxColParams1 = QtGui.QHBoxLayout()
        colStartLabel = QtGui.QLabel('Oscillation Start:')
        colStartLabel.setFixedWidth(140)
        colStartLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.osc_start_ledit = QtGui.QLineEdit()
        self.osc_start_ledit.setFixedWidth(60)
        colEndLabel = QtGui.QLabel('Oscillation Range:')
        colEndLabel.setAlignment(QtCore.Qt.AlignCenter) 
        colEndLabel.setFixedWidth(140)
        self.osc_end_ledit = QtGui.QLineEdit()
        self.osc_end_ledit.setFixedWidth(60)
        self.osc_end_ledit.textChanged[str].connect(self.totalExpChanged)        
        hBoxColParams1.addWidget(colStartLabel)
        hBoxColParams1.addWidget(self.osc_start_ledit)
        hBoxColParams1.addWidget(colEndLabel)
        hBoxColParams1.addWidget(self.osc_end_ledit)
        hBoxColParams2 = QtGui.QHBoxLayout()
        colRangeLabel = QtGui.QLabel('Oscillation Width:')
        colRangeLabel.setFixedWidth(140)
        colRangeLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.osc_range_ledit = QtGui.QLineEdit()
        self.osc_range_ledit.setFixedWidth(60)
        self.osc_range_ledit.textChanged[str].connect(self.totalExpChanged)                
        colExptimeLabel = QtGui.QLabel('ExposureTime:')
        colExptimeLabel.setFixedWidth(140)
        colExptimeLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.exp_time_ledit = QtGui.QLineEdit()
        self.exp_time_ledit.setFixedWidth(60)
        self.exp_time_ledit.textChanged[str].connect(self.totalExpChanged)                
        hBoxColParams2.addWidget(colRangeLabel)
        hBoxColParams2.addWidget(self.osc_range_ledit)
        hBoxColParams2.addWidget(colExptimeLabel)
        hBoxColParams2.addWidget(self.exp_time_ledit)
        hBoxColParams25 = QtGui.QHBoxLayout()
        totalExptimeLabel = QtGui.QLabel('Total Exposure Time (s):')
        totalExptimeLabel.setFixedWidth(155)
        totalExptimeLabel.setAlignment(QtCore.Qt.AlignCenter) 
#        self.totalExptime_ledit = QtGui.QLineEdit()
        self.totalExptime_ledit = QtGui.QLabel()        
        self.totalExptime_ledit.setFixedWidth(60)
        if (daq_utils.beamline == "amx"):                                      
          sampleLifetimeLabel = QtGui.QLabel('Estimated Sample Lifetime (s): ')
          self.sampleLifetimeReadback = QtEpicsPVLabel(daq_utils.pvLookupDict["sampleLifetime"],self,70,2)
          self.sampleLifetimeReadback_ledit = self.sampleLifetimeReadback.getEntry()
        hBoxColParams25.addWidget(totalExptimeLabel)
        hBoxColParams25.addWidget(self.totalExptime_ledit)
        if (daq_utils.beamline == "amx"):                                              
          hBoxColParams25.addWidget(sampleLifetimeLabel)
          hBoxColParams25.addWidget(self.sampleLifetimeReadback_ledit)
        hBoxColParams22 = QtGui.QHBoxLayout()
        colTransmissionLabel = QtGui.QLabel('Transmission (0.0-1.0):')
        colTransmissionLabel.setAlignment(QtCore.Qt.AlignCenter) 
        colTransmissionLabel.setFixedWidth(140)
        self.transmissionReadback = QtEpicsPVLabel(daq_utils.pvLookupDict["transmissionRBV"],self,70,2)
        self.transmissionReadback_ledit = self.transmissionReadback.getEntry()
        transmisionSPLabel = QtGui.QLabel("SetPoint:")
        self.transmissionSetPoint = QtEpicsPVEntry(daq_utils.pvLookupDict["transmissionSet"],self,70,2)
        self.transmission_ledit = self.transmissionSetPoint.getEntry()
        setTransButton = QtGui.QPushButton("Set Trans")
        setTransButton.clicked.connect(self.setTransCB)        
#        if (daq_utils.beamline == "amx"):
#          setTransButton.setEnabled(False)
        hBoxColParams3 = QtGui.QHBoxLayout()
        colEnergyLabel = QtGui.QLabel('Energy (eV):')
        colEnergyLabel.setFixedWidth(100)
        colEnergyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.energyMotorEntry = QtEpicsPVLabel(daq_utils.motor_dict["energy"]+ ".RBV",self,70,2)
        self.energyReadback = self.energyMotorEntry.getEntry()
        energySPLabel = QtGui.QLabel("SetPoint:")
        energySPLabel.setFixedWidth(75)        
        self.energyMoveLedit = QtEpicsPVEntry(daq_utils.motor_dict["energy"] + ".VAL",self,75,2)
        self.energy_ledit = self.energyMoveLedit.getEntry()
        moveEnergyButton = QtGui.QPushButton("Move Energy")
        moveEnergyButton.clicked.connect(self.moveEnergyCB)        
#        self.energyMotorEntry = QtEpicsMotorEntry(daq_utils.motor_dict["energy"],self,70,2)        
#        self.energy_ledit = self.energyMotorEntry.getEntry()        
#        self.energyMotorEntry = QtGui.QLineEdit()
#        self.energyMotorEntry.setFixedWidth(60)
##        self.energyMotorEntry.getEntry().textChanged[str].connect(self.energyTextChanged)
#        hBoxColParams3.addWidget(colTransmissionLabel)
#        hBoxColParams3.addWidget(self.transmission_ledit)
        hBoxColParams3.addWidget(colEnergyLabel)
        hBoxColParams3.addWidget(self.energyReadback)
        hBoxColParams3.addWidget(energySPLabel)        
        hBoxColParams3.addWidget(self.energy_ledit)
        hBoxColParams3.addWidget(moveEnergyButton)
        hBoxColParams22.addWidget(colTransmissionLabel)
        hBoxColParams22.addWidget(self.transmissionReadback_ledit)
        hBoxColParams22.addWidget(transmisionSPLabel)
        hBoxColParams22.addWidget(self.transmission_ledit)
        hBoxColParams22.addWidget(setTransButton)
        hBoxColParams4 = QtGui.QHBoxLayout()
        colBeamWLabel = QtGui.QLabel('Beam Width:')
        colBeamWLabel.setFixedWidth(140)
        colBeamWLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.beamWidth_ledit = QtGui.QLineEdit()
#        self.beamWidth_ledit.textChanged[str].connect(self.beamWidthChangedCB)
        self.beamWidth_ledit.setFixedWidth(60)
        colBeamHLabel = QtGui.QLabel('Beam Height:')
        colBeamHLabel.setFixedWidth(140)
        colBeamHLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.beamHeight_ledit = QtGui.QLineEdit()
#        self.beamHeight_ledit.textChanged[str].connect(self.beamHeightChangedCB)        
        self.beamHeight_ledit.setFixedWidth(60)
        hBoxColParams4.addWidget(colBeamWLabel)
        hBoxColParams4.addWidget(self.beamWidth_ledit)
        hBoxColParams4.addWidget(colBeamHLabel)
        hBoxColParams4.addWidget(self.beamHeight_ledit)
        hBoxColParams5 = QtGui.QHBoxLayout()
        colResoLabel = QtGui.QLabel('Edge Resolution:')
        colResoLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.resolution_ledit = QtGui.QLineEdit()
        self.resolution_ledit.setFixedWidth(60)
        self.resolution_ledit.textEdited[str].connect(self.resoTextChanged)
        detDistLabel = QtGui.QLabel('Detector Dist.')
        detDistLabel.setAlignment(QtCore.Qt.AlignCenter)         
        detDistRBLabel = QtGui.QLabel("Readback:")
        self.detDistRBVLabel = QtEpicsPVLabel(daq_utils.motor_dict["detectorDist"] + ".RBV",self,70) 
        detDistSPLabel = QtGui.QLabel("SetPoint:")
        self.detDistMotorEntry = QtEpicsPVEntry(daq_utils.motor_dict["detectorDist"] + ".VAL",self,70,2)        
#        self.detDistMotorEntry = QtEpicsMotorEntry(daq_utils.motor_dict["detectorDist"],self,70,2)
        self.detDistMotorEntry.getEntry().textChanged[str].connect(self.detDistTextChanged)        
#        self.detDistMotorEntry.setFixedWidth(60)
        self.moveDetDistButton = QtGui.QPushButton("Move Detector")
#        self.moveDetDistButton.setEnabled(False)                
        self.moveDetDistButton.clicked.connect(self.moveDetDistCB)
        hBoxColParams5.addWidget(detDistLabel)
        hBoxColParams5.addWidget(detDistRBLabel)
        hBoxColParams5.addWidget(self.detDistRBVLabel.getEntry())
        hBoxColParams5.addWidget(detDistSPLabel)        
        hBoxColParams5.addWidget(self.detDistMotorEntry.getEntry())
        hBoxColParams5.addWidget(self.moveDetDistButton)        
        hBoxColParams6 = QtGui.QHBoxLayout()
        hBoxColParams6.setAlignment(QtCore.Qt.AlignLeft) 
        hBoxColParams7 = QtGui.QHBoxLayout()
        hBoxColParams7.setAlignment(QtCore.Qt.AlignLeft) 
        centeringLabel = QtGui.QLabel('Sample Centering:')
        centeringLabel.setFixedWidth(140)        
        centeringOptionList = ["Interactive","AutoLoop","AutoRaster","Testing"]
#        centeringOptionList = ["Interactive","Automatic"]
        self.centeringComboBox = QtGui.QComboBox(self)
        self.centeringComboBox.addItems(centeringOptionList)
#        self.centeringComboBox.activated[str].connect(self.ComboActivatedCB) 
        protoLabel = QtGui.QLabel('Protocol:')
        font = QtGui.QFont()
        font.setBold(True)
        protoLabel.setFont(font)
        
        protoLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.protoRadioGroup=QtGui.QButtonGroup()
        self.protoStandardRadio = QtGui.QRadioButton("standard")
        self.protoStandardRadio.setChecked(True)
        self.protoStandardRadio.toggled.connect(functools.partial(self.protoRadioToggledCB,"standard"))
        self.protoStandardRadio.pressed.connect(functools.partial(self.protoRadioToggledCB,"standard"))        
        self.protoRadioGroup.addButton(self.protoStandardRadio)

        self.protoRasterRadio = QtGui.QRadioButton("raster")
        self.protoRasterRadio.toggled.connect(functools.partial(self.protoRadioToggledCB,"raster"))
        self.protoRasterRadio.pressed.connect(functools.partial(self.protoRadioToggledCB,"raster"))                
        self.protoRadioGroup.addButton(self.protoRasterRadio)

        self.protoVectorRadio = QtGui.QRadioButton("vector")
        self.protoRasterRadio.toggled.connect(functools.partial(self.protoRadioToggledCB,"vector"))
        self.protoRasterRadio.pressed.connect(functools.partial(self.protoRadioToggledCB,"vector"))        
        self.protoRadioGroup.addButton(self.protoVectorRadio)

        self.protoOtherRadio = QtGui.QRadioButton("other")
        self.protoOtherRadio.setEnabled(False)
        self.protoRadioGroup.addButton(self.protoOtherRadio)
        

        protoOptionList = ["standard","screen","raster","vector","eScan","stepRaster","stepVector","multiCol","characterize","ednaCol"] # these should probably come from db
#        protoOptionList = ["standard","screen","raster","vector","eScan","stepRaster","stepVector","characterize"] # these should probably come from db        
#        protoOptionList = ["standard","screen","raster","vector","multiCol","multiColQ","eScan","stepRaster","stepVector"] # these should probably come from db 
        self.protoComboBox = QtGui.QComboBox(self)
        self.protoComboBox.addItems(protoOptionList)
        self.protoComboBox.activated[str].connect(self.protoComboActivatedCB) 
        hBoxColParams6.addWidget(protoLabel)
        hBoxColParams6.addWidget(self.protoStandardRadio)
        hBoxColParams6.addWidget(self.protoRasterRadio)
        hBoxColParams6.addWidget(self.protoVectorRadio)        
        hBoxColParams6.addWidget(self.protoComboBox)
        
        hBoxColParams7.addWidget(centeringLabel)
        hBoxColParams7.addWidget(self.centeringComboBox)
        hBoxColParams7.addWidget(colResoLabel)
        hBoxColParams7.addWidget(self.resolution_ledit)
        

        self.processingOptionsFrame = QFrame()
        self.hBoxProcessingLayout1= QtGui.QHBoxLayout()        
        self.hBoxProcessingLayout1.setAlignment(QtCore.Qt.AlignLeft) 
        procOptionLabel = QtGui.QLabel('Processing Options:')
        procOptionLabel.setFixedWidth(200)
        self.fastDPCheckBox = QCheckBox("FastDP")
        self.fastDPCheckBox.setChecked(False)
        self.fastEPCheckBox = QCheckBox("FastEP")
        self.fastEPCheckBox.setChecked(False)
        self.fastEPCheckBox.setEnabled(False)
        self.dimpleCheckBox = QCheckBox("Dimple")
        self.dimpleCheckBox.setChecked(False)        
        self.xia2CheckBox = QCheckBox("Xia2")
        self.xia2CheckBox.setChecked(False)
        self.hBoxProcessingLayout1.addWidget(procOptionLabel)
        self.hBoxProcessingLayout1.addWidget(self.fastDPCheckBox)
        self.hBoxProcessingLayout1.addWidget(self.fastEPCheckBox)
        self.hBoxProcessingLayout1.addWidget(self.dimpleCheckBox)                
        self.hBoxProcessingLayout1.addWidget(self.xia2CheckBox)
        self.processingOptionsFrame.setLayout(self.hBoxProcessingLayout1)

        self.rasterParamsFrame = QFrame()
        self.vBoxRasterParams = QtGui.QVBoxLayout()
        self.hBoxRasterLayout1= QtGui.QHBoxLayout()        
        self.hBoxRasterLayout1.setAlignment(QtCore.Qt.AlignLeft) 
        self.hBoxRasterLayout2= QtGui.QHBoxLayout()        
        self.hBoxRasterLayout2.setAlignment(QtCore.Qt.AlignLeft) 
        rasterStepLabel = QtGui.QLabel('Raster Step')
        rasterStepLabel.setFixedWidth(110)
        self.rasterStepEdit = QtGui.QLineEdit(str(self.rasterStepDefs["Coarse"]))
        self.rasterStepEdit.textChanged[str].connect(self.rasterStepChanged)        
        self.rasterStepEdit.setFixedWidth(60)

        self.rasterGrainRadioGroup=QtGui.QButtonGroup()
        self.rasterGrainCoarseRadio = QtGui.QRadioButton("Coarse")
        self.rasterGrainCoarseRadio.setChecked(False)
        self.rasterGrainCoarseRadio.toggled.connect(functools.partial(self.rasterGrainToggledCB,"Coarse"))
        self.rasterGrainRadioGroup.addButton(self.rasterGrainCoarseRadio)
        self.rasterGrainFineRadio = QtGui.QRadioButton("Fine")
        self.rasterGrainFineRadio.setChecked(False)
        self.rasterGrainFineRadio.toggled.connect(functools.partial(self.rasterGrainToggledCB,"Fine"))
        self.rasterGrainRadioGroup.addButton(self.rasterGrainFineRadio)
        self.rasterGrainVFineRadio = QtGui.QRadioButton("VFine")
        self.rasterGrainVFineRadio.setChecked(False)
        self.rasterGrainVFineRadio.toggled.connect(functools.partial(self.rasterGrainToggledCB,"VFine"))
        self.rasterGrainRadioGroup.addButton(self.rasterGrainVFineRadio)
        self.rasterGrainCustomRadio = QtGui.QRadioButton("Custom")
        self.rasterGrainCustomRadio.setChecked(True)
        self.rasterGrainCustomRadio.toggled.connect(functools.partial(self.rasterGrainToggledCB,"Custom"))
        self.rasterGrainRadioGroup.addButton(self.rasterGrainCustomRadio)

        rasterEvalLabel = QtGui.QLabel('Raster\nEvaluate By:')
        rasterEvalOptionList = ["Spot Count","Resolution","Intensity"]
#        rasterEvalOptionList = db_lib.beamlineInfo(daq_utils.beamline,'rasterScoreFlag')["optionList"]
        self.rasterEvalComboBox = QtGui.QComboBox(self)
        self.rasterEvalComboBox.addItems(rasterEvalOptionList)
        self.rasterEvalComboBox.setCurrentIndex(db_lib.beamlineInfo(daq_utils.beamline,'rasterScoreFlag')["index"])
        self.rasterEvalComboBox.activated[str].connect(self.rasterEvalComboActivatedCB)

        

#        self.rasterStepEdit.setAlignment(QtCore.Qt.AlignLeft) 
        self.hBoxRasterLayout1.addWidget(rasterStepLabel)
#        self.hBoxRasterLayout1.addWidget(self.rasterStepEdit.getEntry())
        self.hBoxRasterLayout1.addWidget(self.rasterStepEdit)
        self.hBoxRasterLayout1.addWidget(self.rasterGrainCoarseRadio)
        self.hBoxRasterLayout1.addWidget(self.rasterGrainFineRadio)
        self.hBoxRasterLayout1.addWidget(self.rasterGrainVFineRadio)        
        self.hBoxRasterLayout1.addWidget(self.rasterGrainCustomRadio)
        self.hBoxRasterLayout2.addWidget(rasterEvalLabel)
        self.hBoxRasterLayout2.addWidget(self.rasterEvalComboBox)
        self.vBoxRasterParams.addLayout(self.hBoxRasterLayout1)
        self.vBoxRasterParams.addLayout(self.hBoxRasterLayout2)        
        
        self.rasterParamsFrame.setLayout(self.vBoxRasterParams)

        self.multiColParamsFrame = QFrame() #something for criteria to decide on which hotspots to collect on for multi-xtal
        self.hBoxMultiColParamsLayout1 = QtGui.QHBoxLayout()
        self.hBoxMultiColParamsLayout1.setAlignment(QtCore.Qt.AlignLeft)
        multiColCutoffLabel = QtGui.QLabel('Diffraction Cutoff')
        multiColCutoffLabel.setFixedWidth(110)
        self.multiColCutoffEdit = QtGui.QLineEdit("320") #may need to store this in DB at some point, it's a silly number for now
        self.multiColCutoffEdit.setFixedWidth(60)
        self.hBoxMultiColParamsLayout1.addWidget(multiColCutoffLabel)
        self.hBoxMultiColParamsLayout1.addWidget(self.multiColCutoffEdit)
        self.multiColParamsFrame.setLayout(self.hBoxMultiColParamsLayout1)
                                           
        self.characterizeParamsFrame = QFrame()
        vBoxCharacterizeParams1 = QtGui.QVBoxLayout()
        self.hBoxCharacterizeLayout1= QtGui.QHBoxLayout() 
        self.characterizeTargetLabel = QtGui.QLabel('Characterization Targets')       
        characterizeResoLabel = QtGui.QLabel('Resolution')
        characterizeResoLabel.setFixedWidth(120)
        characterizeResoLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.characterizeResoEdit = QtGui.QLineEdit("3.0")
        self.characterizeResoEdit.setFixedWidth(60)
        characterizeISIGLabel = QtGui.QLabel('I/Sigma')
        characterizeISIGLabel.setFixedWidth(120)
        characterizeISIGLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.characterizeISIGEdit = QtGui.QLineEdit("2.0")
        self.characterizeISIGEdit.setFixedWidth(60)
        self.hBoxCharacterizeLayout2 = QtGui.QHBoxLayout() 
        characterizeCompletenessLabel = QtGui.QLabel('Completeness')
        characterizeCompletenessLabel.setFixedWidth(120)
        characterizeCompletenessLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.characterizeCompletenessEdit = QtGui.QLineEdit("0.99")
        self.characterizeCompletenessEdit.setFixedWidth(60)
        characterizeMultiplicityLabel = QtGui.QLabel('Multiplicity')
        characterizeMultiplicityLabel.setFixedWidth(120)
        characterizeMultiplicityLabel.setAlignment(QtCore.Qt.AlignCenter) 
        self.characterizeMultiplicityEdit = QtGui.QLineEdit("auto")
        self.characterizeMultiplicityEdit.setFixedWidth(60)
        self.hBoxCharacterizeLayout1.addWidget(characterizeResoLabel)
        self.hBoxCharacterizeLayout1.addWidget(self.characterizeResoEdit)
        self.hBoxCharacterizeLayout1.addWidget(characterizeISIGLabel)
        self.hBoxCharacterizeLayout1.addWidget(self.characterizeISIGEdit)
        self.hBoxCharacterizeLayout2.addWidget(characterizeCompletenessLabel)
        self.hBoxCharacterizeLayout2.addWidget(self.characterizeCompletenessEdit)
        self.hBoxCharacterizeLayout2.addWidget(characterizeMultiplicityLabel)
        self.hBoxCharacterizeLayout2.addWidget(self.characterizeMultiplicityEdit)
        vBoxCharacterizeParams1.addWidget(self.characterizeTargetLabel)
        vBoxCharacterizeParams1.addLayout(self.hBoxCharacterizeLayout1)
        vBoxCharacterizeParams1.addLayout(self.hBoxCharacterizeLayout2)
        self.characterizeParamsFrame.setLayout(vBoxCharacterizeParams1)
        self.vectorParamsFrame = QFrame()
        hBoxVectorLayout1= QtGui.QHBoxLayout() 
        setVectorStartButton = QtGui.QPushButton("Set Start") 
        setVectorStartButton.clicked.connect(self.setVectorStartCB)
        setVectorEndButton = QtGui.QPushButton("Set End") 
        setVectorEndButton.clicked.connect(self.setVectorEndCB)
        vectorFPPLabel = QtGui.QLabel("Number of Steps")
#        vectorFPPLabel = QtGui.QLabel("Frames Per Point")        
        self.vectorFPP_ledit = QtGui.QLineEdit("1")
#        clearVectorButton = QtGui.QPushButton("Clear Vector") 
#        clearVectorButton.clicked.connect(self.clearVectorCB)
        hBoxVectorLayout1.addWidget(setVectorStartButton)
        hBoxVectorLayout1.addWidget(setVectorEndButton)
        hBoxVectorLayout1.addWidget(vectorFPPLabel)
        hBoxVectorLayout1.addWidget(self.vectorFPP_ledit)
#        hBoxVectorLayout1.addWidget(clearVectorButton)
        self.vectorParamsFrame.setLayout(hBoxVectorLayout1)
        vBoxColParams1.addLayout(hBoxColParams1)
        vBoxColParams1.addLayout(hBoxColParams2)
        vBoxColParams1.addLayout(hBoxColParams25)                
        vBoxColParams1.addLayout(hBoxColParams22)        
        vBoxColParams1.addLayout(hBoxColParams3)
###        vBoxColParams1.addLayout(hBoxColParams4)
        vBoxColParams1.addLayout(hBoxColParams5)
        vBoxColParams1.addLayout(hBoxColParams7)
        vBoxColParams1.addLayout(hBoxColParams6)        
#        vBoxColParams1.addLayout(self.hBoxRasterLayout1)
        vBoxColParams1.addWidget(self.rasterParamsFrame)
        vBoxColParams1.addWidget(self.multiColParamsFrame)
        vBoxColParams1.addWidget(self.vectorParamsFrame)
        vBoxColParams1.addWidget(self.characterizeParamsFrame)
        vBoxColParams1.addWidget(self.processingOptionsFrame)
        self.vectorParamsFrame.hide()
#        self.processingOptionsFrame.hide()
        self.rasterParamsFrame.hide()
        self.multiColParamsFrame.hide()
        self.characterizeParamsFrame.hide()
        colParamsGB.setLayout(vBoxColParams1)
        self.dataPathGB = DataLocInfo(self)
        hBoxDisplayOptionLayout= QtGui.QHBoxLayout()        
        self.albulaDispCheckBox = QCheckBox("Display Data (Albula)")
        self.albulaDispCheckBox.setChecked(True)
#        self.albulaDispCheckBox.stateChanged.connect(self.albulaCheckCB)
        hBoxDisplayOptionLayout.addWidget(self.albulaDispCheckBox)
        vBoxMainColLayout.addWidget(colParamsGB)
        vBoxMainColLayout.addWidget(self.dataPathGB)
        vBoxMainColLayout.addLayout(hBoxDisplayOptionLayout)
        self.mainColFrame.setLayout(vBoxMainColLayout)
        self.EScanToolFrame = QFrame()
        vBoxEScanTool = QtGui.QVBoxLayout()
        self.periodicTableTool = QPeriodicTable(butSize=20)
#        self.periodicTableTool = QPeriodicTable(self.EScanToolFrame,butSize=20)        
        self.EScanDataPathGBTool = DataLocInfo(self)
        vBoxEScanTool.addWidget(self.periodicTableTool)
        vBoxEScanTool.addWidget(self.EScanDataPathGBTool)
        self.EScanToolFrame.setLayout(vBoxEScanTool)
        self.mainToolBox.addItem(self.mainColFrame,"Collection Parameters")        
##########        self.mainToolBox.addItem(self.mainColFrame,"Standard Collection")
#################        self.mainToolBox.addItem(self.EScanToolFrame,"Energy Scan")
        editSampleButton = QtGui.QPushButton("Apply Changes") 
        editSampleButton.clicked.connect(self.editSelectedRequestsCB)
        cloneRequestButton = QtGui.QPushButton("Clone Raster Request") 
        cloneRequestButton.clicked.connect(self.cloneRequestCB)
        hBoxPriorityLayout1= QtGui.QHBoxLayout()        
        priorityEditLabel = QtGui.QLabel("Priority Edit")
        priorityTopButton =  QtGui.QPushButton("   >>   ")
        priorityUpButton =   QtGui.QPushButton("   >    ")
        priorityDownButton = QtGui.QPushButton("   <    ")
        priorityBottomButton=QtGui.QPushButton("   <<   ")
        priorityTopButton.clicked.connect(self.topPriorityCB)
        priorityBottomButton.clicked.connect(self.bottomPriorityCB)
        priorityUpButton.clicked.connect(self.upPriorityCB)
        priorityDownButton.clicked.connect(self.downPriorityCB)
        hBoxPriorityLayout1.addWidget(priorityEditLabel)
        hBoxPriorityLayout1.addWidget(priorityBottomButton)
        hBoxPriorityLayout1.addWidget(priorityDownButton)
        hBoxPriorityLayout1.addWidget(priorityUpButton)
        hBoxPriorityLayout1.addWidget(priorityTopButton)
        queueSampleButton = QtGui.QPushButton("Add Requests to Queue") 
        queueSampleButton.clicked.connect(self.addRequestsToAllSelectedCB)
        deleteSampleButton = QtGui.QPushButton("Delete Requests") 
        deleteSampleButton.clicked.connect(functools.partial(self.dewarTree.deleteSelectedCB,0))
        editScreenParamsButton = QtGui.QPushButton("Edit Raster Params...") 
        editScreenParamsButton.clicked.connect(self.editScreenParamsCB)
        vBoxMainSetup.addWidget(self.mainToolBox)
        vBoxMainSetup.addLayout(hBoxPriorityLayout1)
        vBoxMainSetup.addWidget(queueSampleButton)
        vBoxMainSetup.addWidget(editSampleButton)
        vBoxMainSetup.addWidget(cloneRequestButton)        
#        vBoxMainSetup.addWidget(deleteSampleButton)
        vBoxMainSetup.addWidget(editScreenParamsButton)
        self.mainSetupFrame.setLayout(vBoxMainSetup)
        self.VidFrame = QFrame()
        self.VidFrame.setFixedWidth(680)
        vBoxVidLayout= QtGui.QVBoxLayout()
        if (daq_utils.has_xtalview):
          thread.start_new_thread(self.initVideo2,(.25,)) #highMag
          thread.start_new_thread(self.initVideo4,(.25,))          #this sets up highMagDigiZoom
          thread.start_new_thread(self.initVideo3,(.25,))          #this sets up lowMagDigiZoom
#          self.captureFull=cv2.VideoCapture("http://xf17id1c-ioc2.cs.nsls2.local:8007/C1ZOOM.MJPG.mjpg")          
          self.captureLowMag=cv2.VideoCapture(daq_utils.lowMagCamURL)
        else:
          self.captureLowMag = None
          self.captureHighMag = None
          self.captureHighMagZoom = None          
          self.captureLowMagZoom = None          
        time.sleep(5)
        self.capture = self.captureLowMag
        self.timerHutch = QTimer()
        self.timerHutch.timeout.connect(self.timerHutchRefresh)
        self.timerHutch.start(500)
        
        if (daq_utils.has_xtalview):
          self.timerId = self.startTimer(0) #allegedly does this when window event loop is done if this = 0, otherwise milliseconds, but seems to suspend anyway if use milliseconds (confirmed)
          
        self.centeringMarksList = []
        self.rasterList = []
        self.rasterDefList = []
        self.polyPointItems = []
        self.rasterPoly = None
        self.measureLine = None
#        self.scene = QtGui.QGraphicsScene(0,0,564,450,self)
        self.scene = QtGui.QGraphicsScene(0,0,640,512,self)
        hBoxHutchVidsLayout= QtGui.QHBoxLayout()
        self.sceneHutchCorner = QtGui.QGraphicsScene(0,0,320,180,self)
        self.sceneHutchTop = QtGui.QGraphicsScene(0,0,320,180,self)                        
#        self.scene = QtGui.QGraphicsScene(0,0,646,482,self)        
        self.scene.keyPressEvent = self.sceneKey
        self.view = QtGui.QGraphicsView(self.scene)
        self.viewHutchCorner = QtGui.QGraphicsView(self.sceneHutchCorner)
        self.viewHutchTop = QtGui.QGraphicsView(self.sceneHutchTop)                
        self.pixmap_item = QtGui.QGraphicsPixmapItem(None, self.scene)
        self.pixmap_item_HutchCorner = QtGui.QGraphicsPixmapItem(None, self.sceneHutchCorner)
        self.pixmap_item_HutchTop = QtGui.QGraphicsPixmapItem(None, self.sceneHutchTop)                      
        self.pixmap_item.mousePressEvent = self.pixelSelect

#        centerMarkBrush = QtGui.QBrush(QtCore.Qt.red)
        centerMarkBrush = QtGui.QBrush(QtCore.Qt.blue)                
        centerMarkPen = QtGui.QPen(centerMarkBrush,2.0)
        
#old        self.centerMarker = self.scene.addEllipse(daq_utils.screenPixCenterX-3,daq_utils.screenPixCenterY-3,6, 6, centerMarkPen,centerMarkBrush)
###        self.centerMarker = QtGui.QGraphicsEllipseItem(0,0,6,6)
        self.centerMarker = QtGui.QGraphicsSimpleTextItem("+")
        self.centerMarker.setZValue(10.0)
###        self.centerMarker.setPen(centerMarkPen)#don't use the pen for thin '+'
        self.centerMarker.setBrush(centerMarkBrush)
#        font = QtGui.QFont('Serif', 50,weight=0)
        font = QtGui.QFont('DejaVu Sans Light', self.centerMarkerCharSize,weight=0)
        self.centerMarker.setFont(font)        
        self.scene.addItem(self.centerMarker)
        self.centerMarker.setPos(daq_utils.screenPixCenterX-self.centerMarkerCharOffsetX,daq_utils.screenPixCenterY-self.centerMarkerCharOffsetY)

        self.zoomRadioGroup=QtGui.QButtonGroup()
        self.zoom1Radio = QtGui.QRadioButton("Zoom1")
        self.zoom1Radio.setChecked(True)
        self.zoom1Radio.toggled.connect(functools.partial(self.zoomLevelToggledCB,"Zoom1"))
        self.zoomRadioGroup.addButton(self.zoom1Radio)
        self.zoom2Radio = QtGui.QRadioButton("Zoom2")
        self.zoom2Radio.toggled.connect(functools.partial(self.zoomLevelToggledCB,"Zoom2"))
        self.zoomRadioGroup.addButton(self.zoom2Radio)
        self.zoom3Radio = QtGui.QRadioButton("Zoom3")
        self.zoom3Radio.toggled.connect(functools.partial(self.zoomLevelToggledCB,"Zoom3"))
        self.zoomRadioGroup.addButton(self.zoom3Radio)
        self.zoom4Radio = QtGui.QRadioButton("Zoom4")
        self.zoom4Radio.toggled.connect(functools.partial(self.zoomLevelToggledCB,"Zoom4"))
        self.zoomRadioGroup.addButton(self.zoom4Radio)

        beamOverlayPen = QtGui.QPen(QtCore.Qt.red)
        self.tempBeamSizeXMicrons = 30
        self.tempBeamSizeYMicrons = 30        
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.overlayPosOffsetX = self.centerMarkerCharOffsetX-1
        self.overlayPosOffsetY = self.centerMarkerCharOffsetY-1     
        self.beamSizeOverlay = QtGui.QGraphicsRectItem(self.centerMarker.x()-self.overlayPosOffsetX,self.centerMarker.y()-self.overlayPosOffsetY,self.beamSizeXPixels,self.beamSizeYPixels)
        self.beamSizeOverlay.setPen(beamOverlayPen)
        self.scene.addItem(self.beamSizeOverlay)
        self.beamSizeOverlay.setVisible(False)
#        print(self.centerMarker.x())
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
#        self.centerMarker.setPos(317.0,253.0)

        scaleBrush = QtGui.QBrush(QtCore.Qt.blue)        
        scalePen = QtGui.QPen(scaleBrush,2.0)

        scaleTextPen = QtGui.QPen(scaleBrush,1.0)

        self.imageScaleLineLen = 50
        self.imageScale = self.scene.addLine(10,daq_utils.screenPixY-30,10+self.imageScaleLineLen, daq_utils.screenPixY-30, scalePen)
        self.imageScaleText = self.scene.addSimpleText("50 microns",font=QtGui.QFont("Times", 13))        
        self.imageScaleText.setPen(scaleTextPen)
#        self.imageScaleText.setBrush(scaleBrush)
        self.imageScaleText.setPos(10,450)

        self.click_positions = []
        self.vectorStartFlag = 0
#        self.vectorPointsList = []
        hBoxHutchVidsLayout.addWidget(self.viewHutchTop)
        hBoxHutchVidsLayout.addWidget(self.viewHutchCorner)        
        vBoxVidLayout.addLayout(hBoxHutchVidsLayout)
        vBoxVidLayout.addWidget(self.view)        
        hBoxSampleOrientationLayout = QtGui.QHBoxLayout()
        setDC2CPButton = QtGui.QPushButton("SetStart")
        setDC2CPButton.clicked.connect(self.setDCStartCB)        
        omegaLabel = QtGui.QLabel("Omega:")
        omegaMonitorPV = str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"omegaMonitorPV"))
#        omegaRBLabel = QtGui.QLabel("Readback:")
        self.sampleOmegaRBVLedit = QtEpicsPVLabel(daq_utils.motor_dict["omega"] + "." + omegaMonitorPV,self,70) 
#        self.sampleOmegaRBVLedit = QtEpicsPVLabel(daq_utils.motor_dict["omega"] + ".RBV",self,70) #creates a video lag   
        omegaSPLabel = QtGui.QLabel("SetPoint:")
        self.sampleOmegaMoveLedit = QtEpicsPVEntry(daq_utils.motor_dict["omega"] + ".VAL",self,70,2)
        moveOmegaButton = QtGui.QPushButton("Move")
        moveOmegaButton.clicked.connect(self.moveOmegaCB)
        omegaTweakNegButtonFine = QtGui.QPushButton("-5")        
        omegaTweakNegButton = QtGui.QPushButton("<")
        omegaTweakNegButton.clicked.connect(self.omegaTweakNegCB)
        omegaTweakNegButtonFine.clicked.connect(functools.partial(self.omegaTweakCB,-5))
        self.omegaTweakVal_ledit = QtGui.QLineEdit()
        self.omegaTweakVal_ledit.setFixedWidth(60)
        self.omegaTweakVal_ledit.setText("90")
        omegaTweakPosButtonFine = QtGui.QPushButton("+5")        
        omegaTweakPosButton = QtGui.QPushButton(">")
        omegaTweakPosButton.clicked.connect(self.omegaTweakPosCB)
        omegaTweakPosButtonFine.clicked.connect(functools.partial(self.omegaTweakCB,5))
        hBoxSampleOrientationLayout.addWidget(setDC2CPButton)
        hBoxSampleOrientationLayout.addWidget(omegaLabel)
#        hBoxSampleOrientationLayout.addWidget(omegaRBLabel)
        hBoxSampleOrientationLayout.addWidget(self.sampleOmegaRBVLedit.getEntry())
        hBoxSampleOrientationLayout.addWidget(omegaSPLabel)
        hBoxSampleOrientationLayout.addWidget(self.sampleOmegaMoveLedit.getEntry())
        hBoxSampleOrientationLayout.addWidget(moveOmegaButton)
        spacerItem = QtGui.QSpacerItem(100, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        hBoxSampleOrientationLayout.addItem(spacerItem)
        hBoxSampleOrientationLayout.addWidget(omegaTweakNegButtonFine)
        hBoxSampleOrientationLayout.addWidget(omegaTweakNegButton)        
        hBoxSampleOrientationLayout.addWidget(self.omegaTweakVal_ledit)
        hBoxSampleOrientationLayout.addWidget(omegaTweakPosButton)
        hBoxSampleOrientationLayout.addWidget(omegaTweakPosButtonFine)        
        hBoxSampleOrientationLayout.addStretch(1)
        hBoxVidControlLayout = QtGui.QHBoxLayout()
        lightLevelLabel = QtGui.QLabel("BackLight:")
        lightLevelLabel.setAlignment(QtCore.Qt.AlignRight|Qt.AlignVCenter)         
        sampleBrighterButton = QtGui.QPushButton("+")
        sampleBrighterButton.clicked.connect(self.lightUpCB)
        sampleDimmerButton = QtGui.QPushButton("-")
        sampleDimmerButton.clicked.connect(self.lightDimCB)
        magLevelLabel = QtGui.QLabel("Vid:")
        snapshotButton = QtGui.QPushButton("SnapShot")
        snapshotButton.clicked.connect(self.saveVidSnapshotButtonCB)
#        snapshotButton.setEnabled(False)
        hBoxVidControlLayout.addWidget(magLevelLabel)
        hBoxVidControlLayout.addWidget(self.zoom1Radio)
        hBoxVidControlLayout.addWidget(self.zoom2Radio)
        hBoxVidControlLayout.addWidget(self.zoom3Radio)
        hBoxVidControlLayout.addWidget(self.zoom4Radio)
        hBoxVidControlLayout.addWidget(snapshotButton)
        hBoxVidControlLayout.addWidget(lightLevelLabel)
        hBoxVidControlLayout.addWidget(sampleBrighterButton)
        hBoxVidControlLayout.addWidget(sampleDimmerButton)
        hBoxSampleAlignLayout = QtGui.QHBoxLayout()
        centerLoopButton = QtGui.QPushButton("Center\nLoop")
        centerLoopButton.clicked.connect(self.autoCenterLoopCB)
##        centerLoopButton.setEnabled(False)                        
##        rasterLoopButton = QtGui.QPushButton("Raster\nLoop")
##        rasterLoopButton.clicked.connect(self.autoRasterLoopCB)
        measureButton = QtGui.QPushButton("Measure")
        measureButton.clicked.connect(self.measurePolyCB)
        loopShapeButton = QtGui.QPushButton("Add Raster\nto Queue")
#        loopShapeButton = QtGui.QPushButton("Draw\nRaster")        
        loopShapeButton.clicked.connect(self.drawInteractiveRasterCB)
        runRastersButton = QtGui.QPushButton("Run\nRaster")
        runRastersButton.clicked.connect(self.runRastersCB)
        clearGraphicsButton = QtGui.QPushButton("Clear")
        clearGraphicsButton.clicked.connect(self.eraseCB)
        self.click3Button = QtGui.QPushButton("3-Click\nCenter")
        self.click3Button.clicked.connect(self.center3LoopCB)
        self.threeClickCount = 0
        saveCenteringButton = QtGui.QPushButton("Save\nCenter")
#        saveCenteringButton.setEnabled(False)        
        saveCenteringButton.clicked.connect(self.saveCenterCB)
        selectAllCenteringButton = QtGui.QPushButton("Select All\nCenterings")
#        selectAllCenteringButton.setEnabled(False)                
        selectAllCenteringButton.clicked.connect(self.selectAllCenterCB)
        hBoxSampleAlignLayout.addWidget(centerLoopButton)
#        hBoxSampleAlignLayout.addWidget(rasterLoopButton)
##        hBoxSampleAlignLayout.addWidget(loopShapeButton)
##### for now, until I figure out what people want        hBoxSampleAlignLayout.addWidget(measureButton)        
###        hBoxSampleAlignLayout.addWidget(runRastersButton) #maybe not a good idea to have multiple ways to run a raster. Force the collect button.
        hBoxSampleAlignLayout.addWidget(clearGraphicsButton)
        hBoxSampleAlignLayout.addWidget(saveCenteringButton)
        hBoxSampleAlignLayout.addWidget(selectAllCenteringButton)
        hBoxSampleAlignLayout.addWidget(self.click3Button)        
        hBoxRadioLayout100= QtGui.QHBoxLayout()
        vidActionLabel = QtGui.QLabel("Video Click Mode:")        
        self.vidActionRadioGroup=QtGui.QButtonGroup()
        self.vidActionC2CRadio = QtGui.QRadioButton("C2C")
        self.vidActionC2CRadio.setChecked(True)
        self.vidActionC2CRadio.toggled.connect(self.vidActionToggledCB)
        self.vidActionRadioGroup.addButton(self.vidActionC2CRadio)        
        self.vidActionDefineCenterRadio = QtGui.QRadioButton("Define Center")
        self.vidActionDefineCenterRadio.setChecked(False)
        self.vidActionDefineCenterRadio.setEnabled(False)        
        self.vidActionDefineCenterRadio.toggled.connect(self.vidActionToggledCB)
        self.vidActionRadioGroup.addButton(self.vidActionDefineCenterRadio)
        self.vidActionRasterExploreRadio = QtGui.QRadioButton("Raster Explore")
        self.vidActionRasterExploreRadio.setChecked(False)
        self.vidActionRasterExploreRadio.toggled.connect(self.vidActionToggledCB)
        self.vidActionRadioGroup.addButton(self.vidActionRasterExploreRadio)
        self.vidActionRasterSelectRadio = QtGui.QRadioButton("Raster Select")
        self.vidActionRasterSelectRadio.setChecked(False)
        self.vidActionRasterSelectRadio.toggled.connect(self.vidActionToggledCB)
#        self.vidActionRadioGroup.addButton(self.vidActionRasterSelectRadio)
        self.vidActionRasterDefRadio = QtGui.QRadioButton("Define Raster")
        self.vidActionRasterDefRadio.setChecked(False)
        self.vidActionRasterDefRadio.setEnabled(False)
        self.vidActionRasterDefRadio.toggled.connect(self.vidActionToggledCB)
        self.vidActionRadioGroup.addButton(self.vidActionRasterDefRadio)


#        self.vidActionRasterMoveRadio = QtGui.QRadioButton("RasterMove")
#        self.vidActionRasterMoveRadio.toggled.connect(self.vidActionToggledCB)
#        self.vidActionRadioGroup.addButton(self.vidActionRasterMoveRadio)
        hBoxRadioLayout100.addWidget(vidActionLabel)
        hBoxRadioLayout100.addWidget(self.vidActionC2CRadio)
        hBoxRadioLayout100.addWidget(self.vidActionRasterExploreRadio)
#        hBoxRadioLayout100.addWidget(self.vidActionRasterSelectRadio)
        hBoxRadioLayout100.addWidget(self.vidActionRasterDefRadio)
        hBoxRadioLayout100.addWidget(self.vidActionDefineCenterRadio)                
#        hBoxRadioLayout100.addWidget(self.vidActionPolyRasterDefRadio)
#######        hBoxRadioLayout100.addWidget(self.vidActionRasterMoveRadio)
##        vBoxDFlayout.addLayout(hBoxRadioLayout1)                   
        vBoxVidLayout.addLayout(hBoxSampleOrientationLayout)
        vBoxVidLayout.addLayout(hBoxVidControlLayout)
        vBoxVidLayout.addLayout(hBoxSampleAlignLayout)
        vBoxVidLayout.addLayout(hBoxRadioLayout100)
        self.VidFrame.setLayout(vBoxVidLayout)
        splitter11.addWidget(self.mainSetupFrame)
        self.colTabs= QtGui.QTabWidget()        
        self.energyFrame = QFrame()
        vBoxEScanFull = QtGui.QVBoxLayout()
        hBoxEScan = QtGui.QHBoxLayout()
        vBoxEScan = QtGui.QVBoxLayout()
#        self.periodicFrame = QFrame()
#        self.periodicFrame.setLineWidth(1)
####        self.periodicTable = QPeriodicTable(self.energyFrame,butSize=20)
        self.periodicTable = QPeriodicTable(butSize=20)
        self.periodicTable.elementClicked("Se")
        vBoxEScan.addWidget(self.periodicTable)
#        vBoxEScan.addWidget(self.periodicFrame)
        self.EScanDataPathGB = DataLocInfo(self)
        vBoxEScan.addWidget(self.EScanDataPathGB)
        hBoxEScanParams = QtGui.QHBoxLayout()
        hBoxEScanButtons = QtGui.QHBoxLayout()                        
        tempPlotButton = QtGui.QPushButton("Queue Requests")        
        tempPlotButton.clicked.connect(self.queueEnScanCB)
        clearEnscanPlotButton = QtGui.QPushButton("Clear")        
        clearEnscanPlotButton.clicked.connect(self.clearEnScanPlotCB)        
        hBoxEScanButtons.addWidget(clearEnscanPlotButton)
        hBoxEScanButtons.addWidget(tempPlotButton)
        escanStepsLabel = QtGui.QLabel("Steps")        
        self.escan_steps_ledit = QtGui.QLineEdit()
        self.escan_steps_ledit.setText("41")
        escanStepsizeLabel = QtGui.QLabel("Stepsize (EVs)")        
        self.escan_stepsize_ledit = QtGui.QLineEdit()
        self.escan_stepsize_ledit.setText("1")
        hBoxEScanParams.addWidget(escanStepsLabel)
        hBoxEScanParams.addWidget(self.escan_steps_ledit)
        hBoxEScanParams.addWidget(escanStepsizeLabel)
        hBoxEScanParams.addWidget(self.escan_stepsize_ledit)
        hBoxChoochResults = QtGui.QHBoxLayout()
        hBoxChoochResults2 = QtGui.QHBoxLayout()        
        choochResultsLabel = QtGui.QLabel("Chooch Results")
        choochInflLabel = QtGui.QLabel("Infl")
        self.choochInfl = QtGui.QLabel("")
        self.choochInfl.setFixedWidth(70)                
        choochPeakLabel = QtGui.QLabel("Peak")
        self.choochPeak = QtGui.QLabel("")
        self.choochPeak.setFixedWidth(70)
        choochInflFPrimeLabel = QtGui.QLabel("fPrimeInfl")
        self.choochFPrimeInfl = QtGui.QLabel("")
        self.choochFPrimeInfl.setFixedWidth(70)                
        choochInflF2PrimeLabel = QtGui.QLabel("f2PrimeInfl")
        self.choochF2PrimeInfl = QtGui.QLabel("")
        self.choochF2PrimeInfl.setFixedWidth(70)                
        choochPeakFPrimeLabel = QtGui.QLabel("fPrimePeak")
        self.choochFPrimePeak = QtGui.QLabel("")
        self.choochFPrimePeak.setFixedWidth(70)                
        choochPeakF2PrimeLabel = QtGui.QLabel("f2PrimePeak")
        self.choochF2PrimePeak = QtGui.QLabel("")
        self.choochF2PrimePeak.setFixedWidth(70)                
        
        hBoxChoochResults.addWidget(choochResultsLabel)
        hBoxChoochResults.addWidget(choochInflLabel)
        hBoxChoochResults.addWidget(self.choochInfl)        
        hBoxChoochResults.addWidget(choochPeakLabel)
        hBoxChoochResults.addWidget(self.choochPeak)        
        hBoxChoochResults2.addWidget(choochInflFPrimeLabel)
        hBoxChoochResults2.addWidget(self.choochFPrimeInfl)
        hBoxChoochResults2.addWidget(choochInflF2PrimeLabel)                
        hBoxChoochResults2.addWidget(self.choochF2PrimeInfl)        
        hBoxChoochResults2.addWidget(choochPeakFPrimeLabel)
        hBoxChoochResults2.addWidget(self.choochFPrimePeak)
        hBoxChoochResults2.addWidget(choochPeakF2PrimeLabel)                
        hBoxChoochResults2.addWidget(self.choochF2PrimePeak)        
        
        
        vBoxEScan.addLayout(hBoxEScanParams)
        vBoxEScan.addLayout(hBoxEScanButtons)
        vBoxEScan.addLayout(hBoxChoochResults)
        vBoxEScan.addLayout(hBoxChoochResults2)        
#        vBoxEScan.addWidget(clearEnscanPlotButton)
        hBoxEScan.addLayout(vBoxEScan)
        verticalLine = QFrame()
        verticalLine.setFrameStyle(QFrame.VLine)
#        verticalLine.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.EScanGraph = QtBlissGraph(self.energyFrame)
        hBoxEScan.addWidget(verticalLine)
        hBoxEScan.addWidget(self.EScanGraph)
        vBoxEScanFull.addLayout(hBoxEScan)
        self.choochGraph = QtBlissGraph(self.energyFrame)
        vBoxEScanFull.addWidget(self.choochGraph)
#        vBoxEScan.addWidget(self.graph)
        self.energyFrame.setLayout(vBoxEScanFull)
#        self.colTabs.addTab(self.VidFrame,"Sample Control")
        splitter11.addWidget(self.VidFrame)
        self.colTabs.addTab(splitter11,"Sample Control")
        self.colTabs.addTab(self.energyFrame,"Energy Scan")
#        splitter11.addWidget(self.colTabs)
        splitter1.addWidget(self.colTabs)
###        splitter1.addWidget(splitter11)
#        splitterSizes = [500,700]
#        splitter11.setSizes(splitterSizes)
        vBoxlayout.addWidget(splitter1)
        self.lastFileLabel2 = QtGui.QLabel('Last File:')
        self.lastFileLabel2.setFixedWidth(70)
        if (daq_utils.beamline == "amx"):                    
          self.lastFileRBV2 = QtEpicsPVLabel("XF:17IDB-ES:AMX{Det:Eig9M}cam1:FullFileName_RBV",self,0)            
        else:
          self.lastFileRBV2 = QtEpicsPVLabel("XF:17IDC-ES:FMX{Det:Eig16M}cam1:FullFileName_RBV",self,0)            
        fileHBoxLayout = QtGui.QHBoxLayout()
        self.controlMasterCheckBox = QCheckBox("Control Master")
        self.controlMasterCheckBox.stateChanged.connect(self.changeControlMasterCB)
        self.controlMasterCheckBox.setChecked(False)
        fileHBoxLayout.addWidget(self.controlMasterCheckBox)        
        self.statusLabel = QtEpicsPVLabel(daq_utils.beamlineComm+"program_state",self,150,highlight_on_change=False)
        fileHBoxLayout.addWidget(self.statusLabel.getEntry())
        self.shutterStateLabel = QtGui.QLabel('Shutter State:')
#        self.shutterStateLabel.setFixedWidth(200)
        governorMessageLabel = QtGui.QLabel('Governor Message:')
        self.governorMessage = QtEpicsPVLabel(daq_utils.pvLookupDict["governorMessage"],self,150,highlight_on_change=False)
        fileHBoxLayout.addWidget(governorMessageLabel)
        fileHBoxLayout.addWidget(self.governorMessage.getEntry())
        fileHBoxLayout.addWidget(self.shutterStateLabel)
        fileHBoxLayout.addWidget(self.lastFileLabel2)
        fileHBoxLayout.addWidget(self.lastFileRBV2.getEntry())
        vBoxlayout.addLayout(fileHBoxLayout)
        sampleTab.setLayout(vBoxlayout)   
#        self.dewarTree.refreshTreeDewarView()
        self.XRFTab = QtGui.QFrame()        
        XRFhBox = QtGui.QHBoxLayout()
        self.mcafit = McaAdvancedFit(self.XRFTab)
#        self.mcafit = QFrame() #temp for printer issue!
        XRFhBox.addWidget(self.mcafit)
        self.XRFTab.setLayout(XRFhBox)
        self.tabs.addTab(sampleTab,"Collect")
        self.tabs.addTab(self.XRFTab,"XRF Spectrum")
#        self.vidSourceToggledCB("LowMag")
        self.zoomLevelToggledCB("Zoom1")        

    def albulaCheckCB(self,state):
      if state != QtCore.Qt.Checked:
        albulaUtils.albulaClose()
      else:
        albulaUtils.albulaOpen()      

    def rasterGrainToggledCB(self,identifier):
      if (identifier == "Coarse" or identifier == "Fine" or identifier == "VFine"):
        cellSize = self.rasterStepDefs[identifier]                  
        if (1):
#        if (self.rasterGrainCoarseRadio.isChecked()):            
          self.rasterStepEdit.setText(str(cellSize))
          self.beamWidth_ledit.setText(str(cellSize))
          self.beamHeight_ledit.setText(str(cellSize))          



    def vidActionToggledCB(self):
      if (len(self.rasterList) > 0):
   
#        if (self.vidActionRasterMoveRadio.isChecked()):
#          for i in xrange(len(self.rasterList)):
#            self.rasterList[i]["graphicsItem"].setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        if (self.vidActionRasterSelectRadio.isChecked()):
          for i in xrange(len(self.rasterList)):
            if (self.rasterList[i] != None):
              self.rasterList[i]["graphicsItem"].setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)            
        else:
          for i in xrange(len(self.rasterList)):
            if (self.rasterList[i] != None):
              self.rasterList[i]["graphicsItem"].setFlag(QtGui.QGraphicsItem.ItemIsMovable, False)
              self.rasterList[i]["graphicsItem"].setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
#      if (self.vidActionRasterExploreRadio.isChecked()):
#        self.vidActionRasterDefRadio.setEnabled(True)                    
      if (self.vidActionRasterDefRadio.isChecked()):
        self.click_positions = []
###I think I don't need this, it's inactive        self.protoComboBox.setCurrentIndex(self.protoComboBox.findText(str("raster")))
        self.showProtParams()
      if (self.vidActionC2CRadio.isChecked()):        
        self.click_positions = []
        if (self.protoComboBox.findText(str("raster")) == self.protoComboBox.currentIndex() or self.protoComboBox.findText(str("stepRaster")) == self.protoComboBox.currentIndex()):
          self.protoComboBox.setCurrentIndex(self.protoComboBox.findText(str("standard")))
          self.protoComboActivatedCB("standard")          
        self.showProtParams()




    def adjustGraphics4ZoomChange(self,fov):
      imageScaleMicrons = int(round(self.imageScaleLineLen * (fov["x"]/daq_utils.screenPixX)))
      self.imageScaleText.setText(str(imageScaleMicrons) + " microns")
      
#      self.imageScale.len() * (fov["x"]/daq_utils.screenPixX)      
      if (self.rasterList != []):
        saveRasterList = self.rasterList
        self.eraseDisplayCB()
#        for i in xrange(len(self.rasterDefList)): #rasterdef b/c the erase got rid of raster graphics.
        for i in xrange(len(saveRasterList)):
          if (saveRasterList[i] == None): 
            self.rasterList.append(None)
          else:
            rasterXPixels = float(saveRasterList[i]["graphicsItem"].x())
            rasterYPixels = float(saveRasterList[i]["graphicsItem"].y())
            self.rasterXmicrons = rasterXPixels * (fov["x"]/daq_utils.screenPixX)
            self.rasterYmicrons = rasterYPixels * (fov["y"]/daq_utils.screenPixY)
#            print saveRasterList[i]
            self.drawPolyRaster(db_lib.getRequestByID(saveRasterList[i]["uid"]),saveRasterList[i]["coords"]["x"],saveRasterList[i]["coords"]["y"],saveRasterList[i]["coords"]["z"])
            self.fillPolyRaster(db_lib.getRequestByID(saveRasterList[i]["uid"]),takeSnapshot=False)

#            self.drawPolyRaster(self.rasterDefList[i])
###########what about this>>>>>            self.rasterList[i]["graphicsItem"].setPos(self.screenXmicrons2pixels(self.rasterXmicrons),self.screenYmicrons2pixels(self.rasterYmicrons))
            self.processSampMove(self.sampx_pv.get(),"x")
            self.processSampMove(self.sampy_pv.get(),"y")
            self.processSampMove(self.sampz_pv.get(),"z")
            
      if (self.vectorStart != None):
        self.processSampMove(self.sampx_pv.get(),"x")
        self.processSampMove(self.sampy_pv.get(),"y")
        self.processSampMove(self.sampz_pv.get(),"z")
      if (self.centeringMarksList != []):          
        self.processSampMove(self.sampx_pv.get(),"x")
        self.processSampMove(self.sampy_pv.get(),"y")
        self.processSampMove(self.sampz_pv.get(),"z")
#      if (self.centeringMarksList != []):        
      if (0):#this is not needed b/c processSampMove takes care of it
        for i in range (0,len(self.centeringMarksList)):
          markerXPixels = float(self.centeringMarksList[i]["graphicsItem"].x())
          markerYPixels = float(self.centeringMarksList[i]["graphicsItem"].y())
          markerXmicrons = markerXPixels * (fov["x"]/daq_utils.screenPixX)
          markerYmicrons = markerYPixels * (fov["y"]/daq_utils.screenPixY)
          self.centeringMarksList[i]["graphicsItem"].setPos(self.screenXmicrons2pixels(markerXmicrons)-daq_utils.screenPixCenterX-self.centerMarker.x()-self.centerMarkerCharOffsetX,self.screenYmicrons2pixels(markerYmicrons)-daq_utils.screenPixCenterY-self.centerMarker.y()-self.centerMarkerCharOffsetY)

    def flushBuffer(self,vidStream):
      if (vidStream == None):
        return
      for i in range (0,200):
        stime = time.time()              
        vidStream.grab()
        etime = time.time()
        commTime = etime-stime
#        print(str(commTime))
        if (commTime>.01):
          return

    
    def zoomLevelToggledCB(self,identifier):
      fov = {}
      zoomedCursorX = daq_utils.screenPixCenterX-self.centerMarkerCharOffsetX
      zoomedCursorY = daq_utils.screenPixCenterY-self.centerMarkerCharOffsetY
      if (self.zoom2Radio.isChecked()):
        self.flushBuffer(self.captureLowMagZoom)
        self.capture = self.captureLowMagZoom
        fov["x"] = daq_utils.lowMagFOVx/2.0
        fov["y"] = daq_utils.lowMagFOVy/2.0
        unzoomedCursorX = self.lowMagCursorX_pv.get()-self.centerMarkerCharOffsetX
        unzoomedCursorY = self.lowMagCursorY_pv.get()-self.centerMarkerCharOffsetY
        if (unzoomedCursorX*2.0<daq_utils.screenPixCenterX):
          zoomedCursorX = unzoomedCursorX*2.0
        if (unzoomedCursorY*2.0<daq_utils.screenPixCenterY):
          zoomedCursorY = unzoomedCursorY*2.0
        if (unzoomedCursorX-daq_utils.screenPixCenterX>daq_utils.screenPixCenterX/2):
          zoomedCursorX = (unzoomedCursorX*2.0) - daq_utils.screenPixX
        if (unzoomedCursorY-daq_utils.screenPixCenterY>daq_utils.screenPixCenterY/2):
          zoomedCursorY = (unzoomedCursorY*2.0) - daq_utils.screenPixY
        self.centerMarker.setPos(zoomedCursorX,zoomedCursorY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
      elif (self.zoom1Radio.isChecked()):
        self.flushBuffer(self.captureLowMag)
        self.capture = self.captureLowMag
        fov["x"] = daq_utils.lowMagFOVx
        fov["y"] = daq_utils.lowMagFOVy
        self.centerMarker.setPos(self.lowMagCursorX_pv.get()-self.centerMarkerCharOffsetX,self.lowMagCursorY_pv.get()-self.centerMarkerCharOffsetY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
      elif (self.zoom4Radio.isChecked()):
        self.flushBuffer(self.captureHighMagZoom)
        self.capture = self.captureHighMagZoom
        fov["x"] = daq_utils.highMagFOVx/2.0
        fov["y"] = daq_utils.highMagFOVy/2.0
        unzoomedCursorX = self.highMagCursorX_pv.get()-self.centerMarkerCharOffsetX
        unzoomedCursorY = self.highMagCursorY_pv.get()-self.centerMarkerCharOffsetY
        if (unzoomedCursorX*2.0<daq_utils.screenPixCenterX):
          zoomedCursorX = unzoomedCursorX*2.0
        if (unzoomedCursorY*2.0<daq_utils.screenPixCenterY):
          zoomedCursorY = unzoomedCursorY*2.0
        if (unzoomedCursorX-daq_utils.screenPixCenterX>daq_utils.screenPixCenterX/2):
          zoomedCursorX = (unzoomedCursorX*2.0) - daq_utils.screenPixX
        if (unzoomedCursorY-daq_utils.screenPixCenterY>daq_utils.screenPixCenterY/2):
          zoomedCursorY = (unzoomedCursorY*2.0) - daq_utils.screenPixY
        self.centerMarker.setPos(zoomedCursorX,zoomedCursorY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
      elif (self.zoom3Radio.isChecked()):
        self.flushBuffer(self.captureHighMag)
        self.capture = self.captureHighMag
        fov["x"] = daq_utils.highMagFOVx
        fov["y"] = daq_utils.highMagFOVy
        self.centerMarker.setPos(self.highMagCursorX_pv.get()-self.centerMarkerCharOffsetX,self.highMagCursorY_pv.get()-self.centerMarkerCharOffsetY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
      self.adjustGraphics4ZoomChange(fov)
      

    def saveVidSnapshotButtonCB(self): 
      comment,useOlog,ok = snapCommentDialog.getComment()
      if (ok):
        self.saveVidSnapshotCB(comment,useOlog)


    def saveVidSnapshotCBold(self,comment="",reqID=None):
      return #short-circuit
#      totalRect = QtCore.QRectF(self.view.frameRect())
       
#      width = 564
#      height = 450
#      width = 646
#      height = 482
      width=640
      height=512
      targetrect = QRectF(0, 0, width, height)
      sourcerect = QRectF(0, 0, width, height)
#    view.render(painter, targetrect, sourcerect)
#      pix = QtGui.QPixmap(totalRect.width(), totalRect.height())
      pix = QtGui.QPixmap(width, height)
      painter = QtGui.QPainter(pix)
#      self.scene.render(painter, totalRect)
      self.scene.render(painter, targetrect,sourcerect)
      now = time.time()
##      imagePath = os.getcwd()+"/snapshots/capture"+str(int(now))+".jpg" #for olog if I want to use it
##      pix.save(imagePath, "JPG")
      byte_array = QByteArray()
      buffer = QBuffer(byte_array)
      buffer.open(QIODevice.WriteOnly)
      pix.save(buffer, 'JPG')
      string_io = StringIO.StringIO(byte_array)
      string_io.seek(0)
      data = string_io.read()
      resultObj = {}
      imgRef = db_lib.addFile(data)
      resultObj["data"] = imgRef
      resultObj["comment"] = str(comment)
      if (reqID != None): #assuming raster here, but will probably need to check the type
        db_lib.addResultforRequest("rasterJpeg",reqID,owner=daq_utils.owner,result_obj=resultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
      else: # the user pushed the snapshot button on the gui
        mountedSampleID = self.mountedPin_pv.get()
        if (mountedSampleID>-1): #not sure what to do if no sample is mounted
#          newSampleRequest = db_lib.addRequesttoSample(self.mountedPin_pv.get(),"snapshot")
#          db_lib.addResultforRequest("snapshotResult",newSampleRequest["request_id"],resultObj)        
          db_lib.addResulttoSample("snapshotResult",mountedSampleID,resultObj,beamline=daq_utils.beamline)        
#          db_lib.deleteRequest(newSampleRequest)
        else: #beamline result, no sample mounted
          db_lib.addResulttoBL("snapshotResult",daq_utils.beamline,resultObj)        
#      print string_io.read()
###      lsdcOlog.toOlog(imagePath,comment,self.omegaRBV_pv)
      del painter


    def saveVidSnapshotCB(self,comment="",useOlog=False,reqID=None):

#      totalRect = QtCore.QRectF(self.view.frameRect())
      if (not os.path.exists("snapshots")):
        os.system("mkdir snapshots")
      width=640
      height=512
      targetrect = QRectF(0, 0, width, height)
      sourcerect = QRectF(0, 0, width, height)
#    view.render(painter, targetrect, sourcerect)
#      pix = QtGui.QPixmap(totalRect.width(), totalRect.height())
      pix = QtGui.QPixmap(width, height)
      painter = QtGui.QPainter(pix)
#      self.scene.render(painter, totalRect)
      self.scene.render(painter, targetrect,sourcerect)
      painter.end()
      now = time.time()
      if (reqID != None):
        filePrefix = db_lib.getRequestByID(reqID)["request_obj"]["file_prefix"]
        imagePath = os.getcwd()+"/snapshots/"+filePrefix+str(int(now))+".jpg"
      else:
        if (self.dataPathGB.prefix_ledit.text() != ""):            
          imagePath = os.getcwd()+"/snapshots/"+str(self.dataPathGB.prefix_ledit.text())+str(int(now))+".jpg"             
        else:
          imagePath = os.getcwd()+"/snapshots/capture"+str(int(now))+".jpg" 
      pix.save(imagePath, "JPG")
      if (useOlog):
        lsdcOlog.toOlogPicture(imagePath,str(comment))
      resultObj = {}
      imgRef = imagePath #for now, just the path, might want to use filestore later, if they really do facilitate moving files
      resultObj["data"] = imgRef
      resultObj["comment"] = str(comment)
      if (reqID != None): #assuming raster here, but will probably need to check the type
        db_lib.addResultforRequest("rasterJpeg",reqID,owner=daq_utils.owner,result_obj=resultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
      else: # the user pushed the snapshot button on the gui
        mountedSampleID = self.mountedPin_pv.get()
        if (mountedSampleID != ""): 
#          newSampleRequest = db_lib.addRequesttoSample(self.mountedPin_pv.get(),"snapshot")
#          db_lib.addResultforRequest("snapshotResult",newSampleRequest["request_id"],resultObj)        
          db_lib.addResulttoSample("snapshotResult",mountedSampleID,owner=daq_utils.owner,result_obj=resultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline) 
#          db_lib.deleteRequest(newSampleRequest)
        else: #beamline result, no sample mounted
          db_lib.addResulttoBL("snapshotResult",daq_utils.beamline,owner=daq_utils.owner,result_obj=resultObj,proposalID=daq_utils.getProposalID())        
#      print string_io.read()
###      lsdcOlog.toOlog(imagePath,comment,self.omegaRBV_pv)
        
###del painter

      

    def changeControlMasterCB(self, state, processID=os.getpid()): #when someone touches checkbox, either through interaction or code
      print("change control master")
      print(processID)
      currentMaster = self.controlMaster_pv.get()
      if (currentMaster < 0):
        self.controlMaster_pv.put(currentMaster) #this makes sure if things are locked, and someone tries to get control, their checkbox will uncheck itself
#        if (abs(int(self.controlMaster_pv.get())) != processID): #override in place, this user cannot take control
        return
      if (state == QtCore.Qt.Checked):
        self.controlMaster_pv.put(processID)

      
    def calculateNewYCoordPosOld(self,startYX,startYY):
      startY_pixels = 0
      xMotRBV = self.motPos["x"]
      deltaYX = startYX-xMotRBV
      yMotRBV = self.motPos["y"]
      deltaYY = startYY-yMotRBV
      omegaRad = math.radians(self.motPos["omega"])
#      newYX = 0-((float(startY_pixels-(self.screenYmicrons2pixels(deltaYX))))*math.sin(omegaRad))      
      newYX = (float(startY_pixels-(self.screenYmicrons2pixels(deltaYX))))*math.sin(omegaRad)
      newYY = (float(startY_pixels-(self.screenYmicrons2pixels(deltaYY))))*math.cos(omegaRad)
      newY = newYX + newYY
      return newY


    def calculateNewYCoordPosOld2(self,startYX,startYY):
      startY_pixels = 0
      zMotRBV = self.motPos["z"]
#      xMotRBV = self.motPos["x"]
      deltaYX = startYX-zMotRBV
      yMotRBV = self.motPos["y"]
      deltaYY = startYY-yMotRBV
      omegaRad = math.radians(self.motPos["omega"])
#      newYY = 0-((float(startY_pixels-(self.screenYmicrons2pixels(deltaYY))))*math.sin(omegaRad))
      newYY = (float(startY_pixels-(self.screenYmicrons2pixels(deltaYY))))*math.sin(omegaRad)
      newYX = (float(startY_pixels-(self.screenYmicrons2pixels(deltaYX))))*math.cos(omegaRad)
      newY = newYX + newYY
      return newY

    def calculateNewYCoordPos(self,startYX,startYY):
      startY_pixels = 0
      zMotRBV = self.motPos["y"]
#      xMotRBV = self.motPos["x"]
      deltaYX = startYX-zMotRBV
      yMotRBV = self.motPos["z"]
      deltaYY = startYY-yMotRBV
      omegaRad = math.radians(self.motPos["omega"])
#      newYY = 0-((float(startY_pixels-(self.screenYmicrons2pixels(deltaYY))))*math.sin(omegaRad))
      newYY = (float(startY_pixels-(self.screenYmicrons2pixels(deltaYY))))*math.sin(omegaRad)
      newYX = (float(startY_pixels-(self.screenYmicrons2pixels(deltaYX))))*math.cos(omegaRad)
      newY = newYX + newYY
      return newY


    def processROIChange(self,posRBV,ID):
#      print(ID + " changed to " + str(posRBV))
      pass


    def processLowMagCursorChange(self,posRBV,ID):
      zoomedCursorX = daq_utils.screenPixCenterX-self.centerMarkerCharOffsetX
      zoomedCursorY = daq_utils.screenPixCenterY-self.centerMarkerCharOffsetY
      if (self.zoom2Radio.isChecked()):  #lowmagzoom
        unzoomedCursorX = self.lowMagCursorX_pv.get()-self.centerMarkerCharOffsetX
        unzoomedCursorY = self.lowMagCursorY_pv.get()-self.centerMarkerCharOffsetY
        if (unzoomedCursorX*2.0<daq_utils.screenPixCenterX):
          zoomedCursorX = unzoomedCursorX*2.0
        if (unzoomedCursorY*2.0<daq_utils.screenPixCenterY):
          zoomedCursorY = unzoomedCursorY*2.0
        if (unzoomedCursorX-daq_utils.screenPixCenterX>daq_utils.screenPixCenterX/2):
          zoomedCursorX = (unzoomedCursorX*2.0) - daq_utils.screenPixX
        if (unzoomedCursorY-daq_utils.screenPixCenterY>daq_utils.screenPixCenterY/2):           
          zoomedCursorY = (unzoomedCursorY*2.0) - daq_utils.screenPixY
        self.centerMarker.setPos(zoomedCursorX,zoomedCursorY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
      else:
        self.centerMarker.setPos(self.lowMagCursorX_pv.get()-self.centerMarkerCharOffsetX,self.lowMagCursorY_pv.get()-self.centerMarkerCharOffsetY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)


    def processHighMagCursorChange(self,posRBV,ID):
      zoomedCursorX = daq_utils.screenPixCenterX-self.centerMarkerCharOffsetX
      zoomedCursorY = daq_utils.screenPixCenterY-self.centerMarkerCharOffsetY
      if (self.zoom4Radio.isChecked()):      #highmagzoom
        unzoomedCursorX = self.highMagCursorX_pv.get()-self.centerMarkerCharOffsetX
        unzoomedCursorY = self.highMagCursorY_pv.get()-self.centerMarkerCharOffsetY
        if (unzoomedCursorX*2.0<daq_utils.screenPixCenterX):
          zoomedCursorX = unzoomedCursorX*2.0
        if (unzoomedCursorY*2.0<daq_utils.screenPixCenterY):
          zoomedCursorY = unzoomedCursorY*2.0
        if (unzoomedCursorX-daq_utils.screenPixCenterX>daq_utils.screenPixCenterX/2):
          zoomedCursorX = (unzoomedCursorX*2.0) - daq_utils.screenPixX
        if (unzoomedCursorY-daq_utils.screenPixCenterY>daq_utils.screenPixCenterY/2):           
          zoomedCursorY = (unzoomedCursorY*2.0) - daq_utils.screenPixY
        self.centerMarker.setPos(zoomedCursorX,zoomedCursorY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)
      else:
        self.centerMarker.setPos(self.highMagCursorX_pv.get()-self.centerMarkerCharOffsetX,self.highMagCursorY_pv.get()-self.centerMarkerCharOffsetY)
        self.beamSizeXPixels = self.screenXmicrons2pixels(self.tempBeamSizeXMicrons)
        self.beamSizeYPixels = self.screenYmicrons2pixels(self.tempBeamSizeYMicrons)
        self.beamSizeOverlay.setRect(self.overlayPosOffsetX+self.centerMarker.x()-(self.beamSizeXPixels/2),self.overlayPosOffsetY+self.centerMarker.y()-(self.beamSizeYPixels/2),self.beamSizeXPixels,self.beamSizeYPixels)

          
    def processSampMove(self,posRBV,motID):
#      print "new " + motID + " pos=" + str(posRBV)
      self.motPos[motID] = posRBV
      if (len(self.centeringMarksList)>0):
        for i in xrange(len(self.centeringMarksList)):
          if (self.centeringMarksList[i] != None):
            centerMarkerOffsetX = self.centeringMarksList[i]["centerCursorX"]-self.centerMarker.x()
            centerMarkerOffsetY = self.centeringMarksList[i]["centerCursorY"]-self.centerMarker.y()
            if (motID == "x"):
              startX = self.centeringMarksList[i]["sampCoords"]["x"]
              delta = startX-posRBV
              newX = float(self.screenXmicrons2pixels(delta))
              self.centeringMarksList[i]["graphicsItem"].setPos(newX-centerMarkerOffsetX,self.centeringMarksList[i]["graphicsItem"].y())
#            self.centeringMarksList[i]["graphicsItem"].setPos(newX,self.centeringMarksList[i]["graphicsItem"].y())
            if (motID == "y" or motID == "z" or motID == "omega"):
              startYY = self.centeringMarksList[i]["sampCoords"]["z"]
              startYX = self.centeringMarksList[i]["sampCoords"]["y"]
              newY = self.calculateNewYCoordPos(startYX,startYY)
              self.centeringMarksList[i]["graphicsItem"].setPos(self.centeringMarksList[i]["graphicsItem"].x(),newY-centerMarkerOffsetY)
#            self.centeringMarksList[i]["graphicsItem"].setPos(self.centeringMarksList[i]["graphicsItem"].x(),newY)            
      if (len(self.rasterList)>0):
        for i in xrange(len(self.rasterList)):
          if (self.rasterList[i] != None):
            if (motID == "x"):
              startX = self.rasterList[i]["coords"]["x"]
              delta = startX-posRBV
              newX = float(self.screenXmicrons2pixels(delta))
              self.rasterList[i]["graphicsItem"].setPos(newX,self.rasterList[i]["graphicsItem"].y())
            if (motID == "y" or motID == "z"):
              startYY = self.rasterList[i]["coords"]["z"]
              startYX = self.rasterList[i]["coords"]["y"]
              newY = self.calculateNewYCoordPos(startYX,startYY)
              self.rasterList[i]["graphicsItem"].setPos(self.rasterList[i]["graphicsItem"].x(),newY)
            if (motID == "omega"):
              if (abs(posRBV-self.rasterList[i]["coords"]["omega"])%360.0 > 5.0):                  
                self.rasterList[i]["graphicsItem"].setVisible(False)
              else:
                self.rasterList[i]["graphicsItem"].setVisible(True)                  
              startYY = self.rasterList[i]["coords"]["z"]
              startYX = self.rasterList[i]["coords"]["y"]
              newY = self.calculateNewYCoordPos(startYX,startYY)
              self.rasterList[i]["graphicsItem"].setPos(self.rasterList[i]["graphicsItem"].x(),newY)
            
      if (self.vectorStart != None):
        centerMarkerOffsetX = self.vectorStart["centerCursorX"]-self.centerMarker.x()
        centerMarkerOffsetY = self.vectorStart["centerCursorY"]-self.centerMarker.y()
          
        if (motID == "omega"):
          startYY = self.vectorStart["coords"]["z"]
          startYX = self.vectorStart["coords"]["y"]
          newY = self.calculateNewYCoordPos(startYX,startYY)
          self.vectorStart["graphicsitem"].setPos(self.vectorStart["graphicsitem"].x(),newY-centerMarkerOffsetY)
          if (self.vectorEnd != None):
            startYX = self.vectorEnd["coords"]["y"]
            startYY = self.vectorEnd["coords"]["z"]
            newY = self.calculateNewYCoordPos(startYX,startYY)
            self.vectorEnd["graphicsitem"].setPos(self.vectorEnd["graphicsitem"].x(),newY-centerMarkerOffsetY)
        if (motID == "x"):
          startX = self.vectorStart["coords"]["x"]
          delta = startX-posRBV
          newX = float(self.screenXmicrons2pixels(delta))
#                    newX = float(0-(self.screenXmicrons2pixels(delta)))
          self.vectorStart["graphicsitem"].setPos(newX-centerMarkerOffsetX,self.vectorStart["graphicsitem"].y())
          if (self.vectorEnd != None):
            startX = self.vectorEnd["coords"]["x"]
            delta = startX-posRBV
            newX = float(self.screenXmicrons2pixels(delta))
#                        newX = float(0-(self.screenXmicrons2pixels(delta)))
            self.vectorEnd["graphicsitem"].setPos(newX-centerMarkerOffsetX,self.vectorEnd["graphicsitem"].y())
        if (motID == "y" or motID == "z"):
          startYX = self.vectorStart["coords"]["y"]
          startYY = self.vectorStart["coords"]["z"]
          newY = self.calculateNewYCoordPos(startYX,startYY)
          self.vectorStart["graphicsitem"].setPos(self.vectorStart["graphicsitem"].x(),newY-centerMarkerOffsetY)
          if (self.vectorEnd != None):
            startYX = self.vectorEnd["coords"]["y"]
            startYY = self.vectorEnd["coords"]["z"]
            newY = self.calculateNewYCoordPos(startYX,startYY)
            self.vectorEnd["graphicsitem"].setPos(self.vectorEnd["graphicsitem"].x(),newY-centerMarkerOffsetY)
        if (self.vectorEnd != None):
#            self.vecLine.setLine(daq_utils.screenPixCenterX+self.vectorStart["graphicsitem"].x(),daq_utils.screenPixCenterY+self.vectorStart["graphicsitem"].y(),daq_utils.screenPixCenterX+self.vectorEnd["graphicsitem"].x(),daq_utils.screenPixCenterY+self.vectorEnd["graphicsitem"].y())
#####            self.vecLine.setLine(self.centerMarker.x()+self.vectorStart["graphicsitem"].x(),self.centerMarker.y()+self.vectorStart["graphicsitem"].y(),self.centerMarker.x()+self.vectorEnd["graphicsitem"].x(),self.centerMarker.y()+self.vectorEnd["graphicsitem"].y())
          self.vecLine.setLine(self.vectorStart["graphicsitem"].x()+self.vectorStart["centerCursorX"]+self.centerMarkerCharOffsetX,self.vectorStart["graphicsitem"].y()+self.vectorStart["centerCursorY"]+self.centerMarkerCharOffsetY,self.vectorEnd["graphicsitem"].x()+self.vectorStart["centerCursorX"]+self.centerMarkerCharOffsetX,self.vectorEnd["graphicsitem"].y()+self.vectorStart["centerCursorY"]+self.centerMarkerCharOffsetY)

    def queueEnScanCB(self):
#      self.addSampleRequestCB(selectedSampleID=self.selectedSampleID)
      self.protoComboBox.setCurrentIndex(self.protoComboBox.findText(str("eScan")))      
      self.addRequestsToAllSelectedCB()
      self.treeChanged_pv.put(1)      

    def clearEnScanPlotCB(self):
      self.EScanGraph.removeCurves()     
      self.choochGraph.removeCurves()

    def displayXrecRaster(self,xrecRasterFlag):
      self.xrecRasterFlag_pv.put("0")
      if (xrecRasterFlag=="100"):
        for i in xrange(len(self.rasterList)):
          if (self.rasterList[i] != None):
            self.scene.removeItem(self.rasterList[i]["graphicsItem"])
      else:
        print("xrecrasterflag = ")
        print(xrecRasterFlag)
        rasterReq = db_lib.getRequestByID(xrecRasterFlag)
        rasterDef = rasterReq["request_obj"]["rasterDef"]
        if (rasterDef["status"] == 1):
          self.drawPolyRaster(rasterReq)
        elif (rasterDef["status"] == 2):        
          self.fillPolyRaster(rasterReq,takeSnapshot=True)
          self.vidActionRasterExploreRadio.setChecked(True)                    
          self.selectedSampleID = rasterReq["sample"]
#          db_lib.deleteRequest(rasterReq)
          self.treeChanged_pv.put(1) #not sure about this
        else:
          pass


    def processMountedPin(self,mountedPinPos):
#      print "in callback mounted pin = " + str(mountedPinPos)
      self.treeChanged_pv.put(1)

    def processFastShutter(self,shutterVal):
#      print "in callback shutterVal = " + str(shutterVal) + " " + str(self.fastShutterOpenPos_pv.get())
      if (round(shutterVal)==round(self.fastShutterOpenPos_pv.get())):
        self.shutterStateLabel.setText("Shutter State:Open")
        self.shutterStateLabel.setStyleSheet("background-color: red;")        
      else:
        self.shutterStateLabel.setText("Shutter State:Closed")
#        self.shutterStateLabel.setStyleSheet("background-color: green;")
        self.shutterStateLabel.setStyleSheet("background-color: #99FF66;")        



    def processControlMaster(self,controlPID):
      print "in callback controlPID = " + str(controlPID)
      if (abs(int(controlPID)) == self.processID):
        self.controlMasterCheckBox.setChecked(True)
      else:
        self.controlMasterCheckBox.setChecked(False)      

    def processControlMasterNew(self,controlPID):
      print "in callback controlPID = " + str(controlPID)
      if (abs(int(controlPID)) != self.processID):
        self.controlMasterCheckBox.setChecked(False)      

    def processChoochResult(self,choochResultFlag):
      if (choochResultFlag == "0"):
        return
      choochResult = db_lib.getResult(choochResultFlag)
      choochResultObj = choochResult["result_obj"]
      graph_x = choochResultObj["choochInXAxis"]
      graph_y = choochResultObj["choochInYAxis"]      
      self.EScanGraph.setTitle("Chooch PLot")
      self.EScanGraph.newcurve("whatever", graph_x, graph_y)
      self.EScanGraph.replot()
      chooch_graph_x = choochResultObj["choochOutXAxis"]
      chooch_graph_y1 = choochResultObj["choochOutY1Axis"]
      chooch_graph_y2 = choochResultObj["choochOutY2Axis"]      
      self.choochGraph.setTitle("Chooch PLot")
      self.choochGraph.newcurve("spline", chooch_graph_x, chooch_graph_y1)
      self.choochGraph.newcurve("fp", chooch_graph_x, chooch_graph_y2)
      self.choochGraph.replot()
      self.choochInfl.setText(str(choochResultObj["infl"]))
      self.choochPeak.setText(str(choochResultObj["peak"]))
      self.choochFPrimeInfl.setText(str(choochResultObj["fprime_infl"]))
      self.choochFPrimePeak.setText(str(choochResultObj["fprime_peak"]))
      self.choochF2PrimeInfl.setText(str(choochResultObj["f2prime_infl"]))
      self.choochF2PrimePeak.setText(str(choochResultObj["f2prime_peak"]))
      self.choochResultFlag_pv.put("0")


# seems like we should be able to do an aggregate query to mongo for max/min :(
    def getMaxPriority(self):
      orderedRequests = db_lib.getOrderedRequestList(daq_utils.beamline)      
      priorityMax = 0
      for i in xrange(len(orderedRequests)):
        if (orderedRequests[i]["priority"] > priorityMax):
          priorityMax = orderedRequests[i]["priority"]
      return priorityMax

    def getMinPriority(self):
      orderedRequests = db_lib.getOrderedRequestList(daq_utils.beamline)      
      priorityMin = 10000000
      for i in xrange(len(orderedRequests)):
        if ((orderedRequests[i]["priority"] < priorityMin) and orderedRequests[i]["priority"]>0):
          priorityMin = orderedRequests[i]["priority"]
      return priorityMin


    def showProtParams(self):
      protocol = str(self.protoComboBox.currentText())
      self.rasterParamsFrame.hide()
      self.vectorParamsFrame.hide()
      self.characterizeParamsFrame.hide()
      self.processingOptionsFrame.hide()
      self.multiColParamsFrame.hide()
      self.osc_start_ledit.setEnabled(True)
      self.osc_end_ledit.setEnabled(True)
      if (protocol == "raster"):
        self.rasterParamsFrame.show()
        
      elif (protocol == "stepRaster"):
        self.rasterParamsFrame.show()
        self.processingOptionsFrame.show()        
      elif (protocol == "multiCol" or protocol == "multiColQ"):
        self.rasterParamsFrame.show()
        self.multiColParamsFrame.show()
        #        self.vectorParamsFrame.hide()
#        self.characterizeParamsFrame.hide()
      elif (protocol == "screen"):
        pass
#        self.osc_end_ledit.setEnabled(False)          
#        return #SHORT CIRCUIT #why would I short circuit this? - So you don't overwrite what the user wants?
#        self.osc_start_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_phist")))
#        self.osc_end_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_phi_end")))
#        self.osc_range_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_width")))
#        self.exp_time_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_time")))
#        self.energy_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_energy")))
#        self.beamWidth_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_beamWidth")))
#        self.beamHeight_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_beamHeight")))
#        self.resolution_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_reso")))
      elif (protocol == "vector" or protocol == "stepVector"):
        self.vectorParamsFrame.show()
        self.processingOptionsFrame.show()        
      elif (protocol == "characterize" or protocol == "ednaCol"):
        self.characterizeParamsFrame.show()
        self.processingOptionsFrame.show()                
      elif (protocol == "standard"):
        self.processingOptionsFrame.show()
      else:
        pass 

    def rasterStepChanged(self,text):
      self.beamWidth_ledit.setText(text)
      self.beamHeight_ledit.setText(text)



    def totalExpChanged(self,text):
      if (str(self.protoComboBox.currentText()) != "standard" and str(self.protoComboBox.currentText()) != "vector"):
        self.totalExptime_ledit.setText("----")
      else:
        try:
          totalExptime = (float(self.osc_end_ledit.text())/(float(self.osc_range_ledit.text())))*float(self.exp_time_ledit.text())
        except ValueError:
          totalExptime = 0.0
        except TypeError:
          totalExptime = 0.0
        except ZeroDivisionError:
          totalExptime = 0.0
        self.totalExptime_ledit.setText(str(totalExptime))
      

    def resoTextChanged(self,text):
      try:
        dist_s = "%.2f" % (daq_utils.distance_from_reso(daq_utils.det_radius,float(text),daq_utils.energy2wave(float(self.energy_ledit.text())),0))
      except ValueError:
        dist_s = "500.0"
      self.detDistMotorEntry.getEntry().setText(dist_s)

    def detDistTextChanged(self,text):
      try:
        reso_s = "%.2f" % (daq_utils.calc_reso(daq_utils.det_radius,float(text),daq_utils.energy2wave(float(self.energy_ledit.text())),0))
      except ValueError:
        reso_s = "50.0"
      except TypeError:
        reso_s = "50.0"
      self.resolution_ledit.setText(reso_s)
      
    def energyTextChanged(self,text):
      dist_s = "%.2f" % (daq_utils.distance_from_reso(daq_utils.det_radius,float(self.resolution_ledit.text()),float(text),0))
#      dist_s = "%.2f" % (daq_utils.distance_from_reso(daq_utils.det_radius,float(self.resolution_ledit.text()),daq_utils.wave2energy(float(text)),0))
      self.detDistMotorEntry.getEntry().setText(dist_s)

    def protoRadioToggledCB(self, text):
 #     print "protocol from radio= " + str(text)
      if (self.protoStandardRadio.isChecked()):
        self.protoComboBox.setCurrentIndex(self.protoComboBox.findText("standard"))
        self.protoComboActivatedCB(text)        
      elif (self.protoRasterRadio.isChecked()):
        self.protoComboBox.setCurrentIndex(self.protoComboBox.findText("raster"))          
        self.protoComboActivatedCB(text)
      elif (self.protoVectorRadio.isChecked()):
        self.protoComboBox.setCurrentIndex(self.protoComboBox.findText("vector"))          
        self.protoComboActivatedCB(text)
      else:
        pass

    def protoComboActivatedCB(self, text):
#      print "protocol from combo = " + str(text)
      self.showProtParams()
      protocol = str(self.protoComboBox.currentText())
      if (protocol == "raster" or protocol == "stepRaster"):
        self.vidActionRasterDefRadio.setChecked(True)
      else:
        self.vidActionC2CRadio.setChecked(True)
      if (protocol == "raster"):
        self.protoRasterRadio.setChecked(True)
        self.osc_start_ledit.setEnabled(False)
        self.osc_end_ledit.setEnabled(False)
        self.osc_range_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultWidth")))
        self.exp_time_ledit.setText(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTime")))
        
      elif (protocol == "standard"):
        self.protoStandardRadio.setChecked(True)
        screenWidth = float(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_width"))
        screenExptime = float(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_time"))
        self.osc_range_ledit.setText(str(screenWidth))
        self.exp_time_ledit.setText(str(screenExptime))
        self.osc_start_ledit.setEnabled(True)
        self.osc_end_ledit.setEnabled(True)
        
      elif (protocol == "vector"):
        screenWidth = float(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_width"))
        screenExptime = float(db_lib.getBeamlineConfigParam(daq_utils.beamline,"screen_default_time"))
        self.osc_range_ledit.setText(str(screenWidth))
        self.exp_time_ledit.setText(str(screenExptime))
        self.osc_start_ledit.setEnabled(True)
        self.osc_end_ledit.setEnabled(True)
        
        self.protoVectorRadio.setChecked(True)
      else:
        self.protoOtherRadio.setChecked(True)
      self.totalExpChanged("")
            

    def rasterEvalComboActivatedCB(self, text):
#      print "protocol = " + str(text)
      db_lib.beamlineInfo(daq_utils.beamline,'rasterScoreFlag',info_dict={"index":self.rasterEvalComboBox.findText(str(text))})
      if (self.currentRasterCellList != []):
        self.reFillPolyRaster()


    def  popBaseDirectoryDialogCB(self):
#      fname = QtGui.QFileDialog.getExistingDirectory(self, 'Choose Directory', '/home')
      fname = QtGui.QFileDialog.getExistingDirectory(self, 'Choose Directory', '',QtGui.QFileDialog.DontUseNativeDialog)      
      if (fname != ""):
        self.dataPathGB.setBasePath_ledit(fname)


    def popImportDialogCB(self):
      fname = QtGui.QFileDialog.getOpenFileName(self, 'Choose Spreadsheet File', '',filter="*.xls *.xlsx",options=QtGui.QFileDialog.DontUseNativeDialog)      
      if (fname != ""):
        print(fname)
        comm_s = "importSpreadsheet(\""+str(fname)+"\")"
        print(comm_s)
        self.send_to_server(comm_s)
        
    def setUserModeCB(self):
      self.vidActionDefineCenterRadio.setEnabled(False)

    def setExpertModeCB(self):
      self.vidActionDefineCenterRadio.setEnabled(True)
        

    def upPriorityCB(self): #neither of these are very elegant, and might even be glitchy if overused
      currentPriority = self.selectedSampleRequest["priority"]
      if (currentPriority<1):
        return
      orderedRequests = db_lib.getOrderedRequestList(daq_utils.beamline)
      for i in xrange(len(orderedRequests)):
        if (orderedRequests[i]["sample"] == self.selectedSampleRequest["sample"]):
          if (i<2):
            self.topPriorityCB()
          else:
            priority = (orderedRequests[i-2]["priority"] + orderedRequests[i-1]["priority"])/2
            if (currentPriority == priority):
              priority = priority+20
            db_lib.updatePriority(self.selectedSampleRequest["uid"],priority)
      self.treeChanged_pv.put(1)
#      self.dewarTree.refreshTree()
            
      
    def downPriorityCB(self):
      currentPriority = self.selectedSampleRequest["priority"]
      if (currentPriority<1):
        return
      orderedRequests = db_lib.getOrderedRequestList(daq_utils.beamline)
      for i in xrange(len(orderedRequests)):
        if (orderedRequests[i]["sample"] == self.selectedSampleRequest["sample"]):
          if ((len(orderedRequests)-i) < 3):
            self.bottomPriorityCB()
          else:
            priority = (orderedRequests[i+1]["priority"] + orderedRequests[i+2]["priority"])/2
            if (currentPriority == priority):
              priority = priority-20
            db_lib.updatePriority(self.selectedSampleRequest["uid"],priority)
#      self.dewarTree.refreshTree()
      self.treeChanged_pv.put(1)


    def topPriorityCB(self):
      currentPriority = self.selectedSampleRequest["priority"]
      if (currentPriority<1):
        return
      priority = int(self.getMaxPriority())
      priority = priority+100
      db_lib.updatePriority(self.selectedSampleRequest["uid"],priority)
      self.treeChanged_pv.put(1)
#      self.dewarTree.refreshTree()


    def bottomPriorityCB(self):
      currentPriority = self.selectedSampleRequest["priority"]
      if (currentPriority<1):
        return
      priority = int(self.getMinPriority())
      priority = priority-100
      db_lib.updatePriority(self.selectedSampleRequest["uid"],priority)
      self.treeChanged_pv.put(1)
#      self.dewarTree.refreshTree()
      

    def dewarViewToggledCB(self,identifier):
#      self.eraseCB()
      self.selectedSampleRequest = {}
#should probably clear textfields here too
      if (identifier == "dewarView"):
        if (self.dewarViewRadio.isChecked()):
          self.dewarTree.refreshTreeDewarView()
      else:
        if (self.priorityViewRadio.isChecked()):
          self.dewarTree.refreshTreePriorityView()

    def dewarViewToggleCheckCB(self):
      if (self.dewarViewRadio.isChecked()):
        self.dewarTree.refreshTreeDewarView()
      else:
        self.dewarTree.refreshTreePriorityView()

    def moveOmegaCB(self):
      comm_s = "mvaDescriptor(\"omega\"," + str(self.sampleOmegaMoveLedit.getEntry().text()) + ")"
      self.send_to_server(comm_s)

    def moveEnergyCB(self):
      comm_s = "mvaDescriptor(\"energy\"," + str(self.energy_ledit.text()) + ")"
      self.send_to_server(comm_s)

    def setTransCB(self):
      if (float(self.transmission_ledit.text()) > 1.0 or float(self.transmission_ledit.text()) < 0.001):
        self.popupServerMessage("Transmission must be 0.001-1.0")
        return
      comm_s = "setTrans(" + str(self.transmission_ledit.text()) + ")"
      print(comm_s)
      self.send_to_server(comm_s)

    def setDCStartCB(self):
      currentPos = float(self.sampleOmegaRBVLedit.getEntry().text())%360.0
#      sweepStart = float(self.osc_start_ledit.text())
#      sweepEnd = float(self.osc_end_ledit.text())
#      sweepRange = sweepEnd-sweepStart
#      newSweepEnd = currentPos + sweepRange
      self.osc_start_ledit.setText(str(currentPos))
#      self.osc_end_ledit.setText(str(newSweepEnd))
      
      
    def moveDetDistCB(self):
      comm_s = "mvaDescriptor(\"detectorDist\"," + str(self.detDistMotorEntry.getEntry().text()) + ")"
      print(comm_s)
      self.send_to_server(comm_s)

    def omegaTweakNegCB(self):
      tv = float(self.omegaTweakVal_ledit.text())
      tweakVal = 0.0-tv
      if (self.controlEnabled()):
        self.omegaTweak_pv.put(tweakVal)
      else:
        self.popupServerMessage("You don't have control")
        
#      comm_s = "mvrDescriptor(\"omega\",-" + str(tv) + ")"
#      if (self.pauseQueueButton.text() == "Continue"):      
#        self.aux_send_to_server(comm_s)
#      else:
#        self.send_to_server(comm_s)
        
    def omegaTweakPosCB(self):
      tv = float(self.omegaTweakVal_ledit.text())
      if (self.controlEnabled()):
        self.omegaTweak_pv.put(tv)
      else:
        self.popupServerMessage("You don't have control")
      
#      comm_s = "mvrDescriptor(\"omega\"," + str(tv) + ")"
#      if (self.pauseQueueButton.text() == "Continue"):      
#        self.aux_send_to_server(comm_s)
#      else:
#        self.send_to_server(comm_s)


    def omegaTweakCB(self,tv):
      tvf = float(tv)
      if (self.controlEnabled()):
        self.omegaTweak_pv.put(tvf)
      else:
        self.popupServerMessage("You don't have control")
      
      
#      comm_s = "mvrDescriptor(\"omega\"," + str(tv) + ")"

#      if (self.pauseQueueButton.text() == "Continue"):      
#        self.aux_send_to_server(comm_s)
#      else:
#        self.send_to_server(comm_s)

    def omega90CBObsolete(self):
      if (self.pauseQueueButton.text() == "Continue"):      
        self.aux_send_to_server(comm_s)
      else:
        self.send_to_server(comm_s)

    def omegaMinus90CBObsolete(self):
      if (self.pauseQueueButton.text() == "Continue"):      
        self.aux_send_to_server(comm_s)
      else:
        self.send_to_server(comm_s)

    def autoCenterLoopCB(self):
      print "auto center loop"
      self.send_to_server("loop_center_xrec()")
      
    def autoRasterLoopCB(self):
      self.selectedSampleID = self.selectedSampleRequest["sample"]
      comm_s = "autoRasterLoop(" + str(self.selectedSampleID) + ")"
      self.send_to_server(comm_s)
#      self.send_to_server("autoRasterLoop()")

    def runRastersCB(self):
      comm_s = "snakeRaster(" + str(self.selectedSampleRequest["uid"]) + ")"
      self.send_to_server(comm_s)
      
    def drawInteractiveRasterCB(self): # any polygon for now, interactive or from xrec
      for i in xrange(len(self.polyPointItems)):
        self.scene.removeItem(self.polyPointItems[i])
      polyPointItems = []
      pen = QtGui.QPen(QtCore.Qt.red)
      brush = QtGui.QBrush(QtCore.Qt.red)
      points = []
      polyPoints = []      
      if (self.click_positions != []): #use the user clicks
        if (len(self.click_positions) == 2): #draws a single row or column
#          print(str(self.click_positions[0].x()) + " " + str(self.click_positions[0].y()) + " " +str(self.click_positions[1].x()) + " " + str(self.click_positions[1].y()))
          polyPoints.append(self.click_positions[0])
#          if (abs(self.click_positions[0].x()-self.click_positions[1].x())<2): #straight line bug fix
          if (1): #straight line bug fix                        
            point = QtCore.QPointF(self.click_positions[0].x(),self.click_positions[1].y())
          else:
            point = QtCore.QPointF(self.click_positions[0].x(),self.click_positions[1].y())
          polyPoints.append(point)
#          polyPoints.append(self.click_positions[1])
          point = QtCore.QPointF(self.click_positions[0].x()+2,self.click_positions[1].y())
          polyPoints.append(point)          
#          if (abs(self.click_positions[0].x()-self.click_positions[1].x())<2): #straight line bug fix
          if (1):
            point = QtCore.QPointF(self.click_positions[0].x()+2,self.click_positions[0].y())
          else:
            point = QtCore.QPointF(self.click_positions[0].x(),self.click_positions[0].y())
          polyPoints.append(point)
          self.rasterPoly = QtGui.QGraphicsPolygonItem(QtGui.QPolygonF(polyPoints))
        else:
          self.rasterPoly = QtGui.QGraphicsPolygonItem(QtGui.QPolygonF(self.click_positions))
###          for point in self.click_positions:
###            newLoopPoint = QtGui.QGraphicsEllipseItem(point.x(),point.y(),3,3)      
###            self.polyPointItems.append(newLoopPoint)
#            self.polyPointItems.append(self.scene.addEllipse(point.x(), point.y(), 2, 2, pen))
      else:
        return
      self.polyBoundingRect = self.rasterPoly.boundingRect()
#      penBlue = QtGui.QPen(QtCore.Qt.blue)
#      self.scene.addRect(self.polyBoundingRect,penBlue) #really don't need this
      raster_w = int(self.polyBoundingRect.width())
      raster_h = int(self.polyBoundingRect.height())
      center_x = int(self.polyBoundingRect.center().x())
      center_y = int(self.polyBoundingRect.center().y())
      stepsizeXPix = self.screenXmicrons2pixels(float(self.rasterStepEdit.text()))
      stepsizeYPix = self.screenYmicrons2pixels(float(self.rasterStepEdit.text()))      
#      print "stepsize = " + str(stepsize)
      self.click_positions = []
      self.definePolyRaster(raster_w,raster_h,stepsizeXPix,stepsizeYPix,center_x,center_y)


    def measurePolyCB(self):
      for i in xrange(len(self.polyPointItems)):
        self.scene.removeItem(self.polyPointItems[i])
      if (self.measureLine != None):
        self.scene.removeItem(self.measureLine)
      self.polyPointItems = []
        
      pen = QtGui.QPen(QtCore.Qt.red)
      brush = QtGui.QBrush(QtCore.Qt.red)
      points = []
      if (self.click_positions != []): #use the user clicks
        if (len(self.click_positions) == 2): #draws a single row or column
          self.measureLine = self.scene.addLine(self.click_positions[0].x(),self.click_positions[0].y(),self.click_positions[1].x(),self.click_positions[1].y(), pen)
      length = self.measureLine.line().length()
      fov = self.getCurrentFOV()
      lineMicronsX = int(round(length * (fov["x"]/daq_utils.screenPixX)))
      print("linelength = " + str(lineMicronsX))      
      self.click_positions = []

      
    def center3LoopCB(self):
      print "3-click center loop"
      self.threeClickCount = 1
      self.click3Button.setStyleSheet("background-color: yellow")
      self.send_to_server("mvaDescriptor(\"omega\",0)")
      

    def fillPolyRaster(self,rasterReq,takeSnapshot=False): #at this point I should have a drawn polyRaster
      time.sleep(1)
#####old      (rasterListIndex,rasterDef) = db_lib.getNextDisplayRaster()
      print "filling poly for " + str(rasterReq["uid"])
###      print(db_lib.getResultsforRequest(rasterReq["uid"]))
      resultCount = len(db_lib.getResultsforRequest(rasterReq["uid"]))
      rasterResults = db_lib.getResultsforRequest(rasterReq["uid"])
      rasterResult = {}
      for i in range (0,len(rasterResults)):
        if (rasterResults[i]['result_type'] == 'rasterResult'):
          rasterResult = rasterResults[i]
          break
      rasterDef = rasterReq["request_obj"]["rasterDef"]
      rasterListIndex = 0
      for i in xrange(len(self.rasterList)):
        if (self.rasterList[i] != None):
          if (self.rasterList[i]["uid"] == rasterReq["uid"]):
            rasterListIndex = i
      if (rasterResult == {}):
        return
      currentRasterGroup = self.rasterList[rasterListIndex]["graphicsItem"]
#      print len(currentRasterGroup.childItems())
      self.currentRasterCellList = currentRasterGroup.childItems()
      cellResults = rasterResult["result_obj"]["rasterCellResults"]['resultObj']
#      cellResults = db_lib.getResultsforRequest(rasterReq["uid"])[resultCount-1]["result_obj"]["rasterCellResults"]['resultObj']      

      numLines = len(cellResults)
      cellResults_array = [{} for i in xrange(numLines)]
#      filename_array = ["" for i in xrange(numLines)]
      my_array = np.zeros(numLines)
      spotLineCounter = 0
      cellIndex=0
      rowStartIndex = 0
      rasterEvalOption = str(self.rasterEvalComboBox.currentText())
      for i in xrange(len(rasterDef["rowDefs"])): #this is building up "my_array" with the rasterEvalOption result, and numpy can then be run against the array. 2/16, I think cellResultsArray not needed
        rowStartIndex = spotLineCounter
        numsteps = rasterDef["rowDefs"][i]["numsteps"]
        for j in xrange(numsteps):
          try:
            cellResult = cellResults[spotLineCounter]
          except IndexError:
            print("caught index error #1")
            print("numlines = " + str(numLines))
            print("expected: " + str(len(rasterDef["rowDefs"])*numsteps))
            return #means a raster failure, and not enough data to cover raster, caused a gui crash
          try:
            spotcount = cellResult["spot_count_no_ice"]
            filename =  cellResult["image"]            
          except TypeError:
            spotcount = 0
            filename = "empty"

          if (i%2 == 0): #this is trying to figure out row direction
            cellIndex = spotLineCounter
          else:
            cellIndex = rowStartIndex + ((numsteps-1)-j)
          try:
            if (rasterEvalOption == "Spot Count"):
              my_array[cellIndex] = spotcount 
            elif (rasterEvalOption == "Intensity"):
              my_array[cellIndex] = cellResult["total_intensity"]
            else:
              if (float(cellResult["d_min"]) == -1):
                my_array[cellIndex] = 50.0
              else:
                my_array[cellIndex] = float(cellResult["d_min"])
          except IndexError:
            print("caught index error #2")
            print("numlines = " + str(numLines))
            print("expected: " + str(len(rasterDef["rowDefs"])*numsteps))
            return #means a raster failure, and not enough data to cover raster, caused a gui crash
          cellResults_array[cellIndex] = cellResult #instead of just grabbing filename, get everything. Not sure why I'm building my own list of results. How is this different from cellResults?
#I don't think cellResults_array is different from cellResults, could maybe test that below by subtituting one for the other. It may be a remnant of trying to store less than the whole result set.          
          spotLineCounter+=1
#  plt.text(int_w+.6,int_h+.5, str(spotcount), size=10,ha="right", va="top", color='r')
      floor = np.amin(my_array)
      ceiling = np.amax(my_array)
      cellCounter = 0     
      for i in xrange(len(rasterDef["rowDefs"])):
        rowCellCount = 0
        for j in xrange(rasterDef["rowDefs"][i]["numsteps"]):
##          spotcount = int(my_array[cellCounter])
##          cellResultsArrayIndex = cellCounter
          cellResult = cellResults_array[cellCounter]
          try:
            spotcount = int(cellResult["spot_count_no_ice"])
            cellFilename = cellResult["image"]
            d_min =  float(cellResult["d_min"])
            if (d_min == -1):
              d_min = 50.0 #trying to handle frames with no spots
            total_intensity =  int(cellResult["total_intensity"])
          except TypeError:
            spotcount = 0
            cellFilename = "empty"
            d_min =  50.0
            total_intensity = 0
              
          if (rasterEvalOption == "Spot Count"):
            param = spotcount 
          elif (rasterEvalOption == "Intensity"):
            param = total_intensity
          else:
            param = d_min
          if (ceiling == 0):
            color_id = 255
          else:
            if (rasterEvalOption == "Resolution"):
              color_id = int(255.0*(float(param-floor)/float(ceiling-floor)))
            else:
              color_id = int(255-(255.0*(float(param-floor)/float(ceiling-floor))))
          self.currentRasterCellList[cellCounter].setBrush(QtGui.QBrush(QtGui.QColor(0,255-color_id,0,127)))
#          self.currentRasterCellList[cellCounter].setBrush(QtGui.QBrush(QtGui.QColor(255-color_id,255-color_id,0,127)))          #yellow
#          self.currentRasterCellList[cellCounter].setBrush(QtGui.QBrush(QtGui.QColor(color_id,color_id,color_id,127)))          
          self.currentRasterCellList[cellCounter].setData(0,spotcount)
          self.currentRasterCellList[cellCounter].setData(1,cellFilename)
          self.currentRasterCellList[cellCounter].setData(2,d_min)
          self.currentRasterCellList[cellCounter].setData(3,total_intensity)
          cellCounter+=1
      if (takeSnapshot):    
        self.saveVidSnapshotCB("Raster Result from sample " + str(rasterReq["request_obj"]["file_prefix"]),useOlog=False,reqID=rasterReq["uid"])



    def reFillPolyRaster(self):      
      rasterEvalOption = str(self.rasterEvalComboBox.currentText())
      for i in xrange(len(self.rasterList)):
        if (self.rasterList[i] != None):
          currentRasterGroup = self.rasterList[i]["graphicsItem"]
          currentRasterCellList = currentRasterGroup.childItems()          
          my_array = np.zeros(len(currentRasterCellList))
          for i in range (0,len(currentRasterCellList)): #first loop is to get floor and ceiling
            cellIndex = i
            if (rasterEvalOption == "Spot Count"):
              spotcount = currentRasterCellList[i].data(0).toInt()[0]
              my_array[cellIndex] = spotcount 
            elif (rasterEvalOption == "Intensity"):
              total_intensity  = currentRasterCellList[i].data(3).toInt()[0]
              my_array[cellIndex] = total_intensity
            else:
              d_min = currentRasterCellList[i].data(2).toDouble()[0]
              if (d_min == -1):
                d_min = 50.0 #trying to handle frames with no spots
              my_array[cellIndex] = d_min
          floor = np.amin(my_array)
          ceiling = np.amax(my_array)
          for i in range (0,len(currentRasterCellList)):
            if (rasterEvalOption == "Spot Count"):
              spotcount = currentRasterCellList[i].data(0).toInt()[0]
              param = spotcount 
            elif (rasterEvalOption == "Intensity"):
              total_intensity  = currentRasterCellList[i].data(3).toInt()[0]
              param = total_intensity
            else:
              d_min = currentRasterCellList[i].data(2).toDouble()[0]
              if (d_min == -1):
                d_min = 50.0 #trying to handle frames with no spots
              param = d_min
            if (ceiling == 0):
              color_id = 255
            if (rasterEvalOption == "Resolution"):
              color_id = int(255.0*(float(param-floor)/float(ceiling-floor)))
            else:
              color_id = int(255-(255.0*(float(param-floor)/float(ceiling-floor))))
            currentRasterCellList[i].setBrush(QtGui.QBrush(QtGui.QColor(0,255-color_id,0,127)))
#            currentRasterCellList[i].setBrush(QtGui.QBrush(QtGui.QColor(color_id,color_id,color_id,127)))            

      
        
    def saveCenterCB(self):
      pen = QtGui.QPen(QtCore.Qt.magenta)
      brush = QtGui.QBrush(QtCore.Qt.magenta)
      markWidth = 10
      marker = self.scene.addEllipse(self.centerMarker.x()-(markWidth/2.0)-1+self.centerMarkerCharOffsetX,self.centerMarker.y()-(markWidth/2.0)-1+self.centerMarkerCharOffsetY,markWidth,markWidth,pen,brush)
#      marker = self.scene.addEllipse(daq_utils.screenPixCenterX-(markWidth/2),daq_utils.screenPixCenterY-(markWidth/2),markWidth,markWidth,pen,brush)      
      marker.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)            
      self.centeringMark = {"sampCoords":{"x":self.sampx_pv.get(),"y":self.sampy_pv.get(),"z":self.sampz_pv.get()},"graphicsItem":marker,"centerCursorX":self.centerMarker.x(),"centerCursorY":self.centerMarker.y()}
      self.centeringMarksList.append(self.centeringMark)
 

    def selectAllCenterCB(self):
      print "select all center"
      for i in xrange(len(self.centeringMarksList)):
        self.centeringMarksList[i]["graphicsItem"].setSelected(True)        


    def lightUpCB(self):
      self.send_to_server("backlightBrighter()")      

    def lightDimCB(self):
      self.send_to_server("backlightDimmer()")              
      

    def eraseCB(self):
      self.click_positions = []
      if (self.measureLine != None):
        self.scene.removeItem(self.measureLine)
      for i in xrange(len(self.centeringMarksList)):
        self.scene.removeItem(self.centeringMarksList[i]["graphicsItem"])        
      self.centeringMarksList = []
      for i in xrange(len(self.polyPointItems)):
        self.scene.removeItem(self.polyPointItems[i])
      self.polyPointItems = []
      if (self.rasterList != []):
        for i in xrange(len(self.rasterList)):
          if (self.rasterList[i] != None):
            self.scene.removeItem(self.rasterList[i]["graphicsItem"])
        self.rasterList = []
        self.rasterDefList = []
        self.currentRasterCellList = []
      self.clearVectorCB()
      if (self.rasterPoly != None):      
        self.scene.removeItem(self.rasterPoly)
      self.rasterPoly =  None


    def eraseDisplayCB(self): #use this for things like zoom change. This is not the same as getting rid of all rasters.
      if (self.rasterList != []):
        for i in xrange(len(self.rasterList)):
          if (self.rasterList[i] != None):
            self.scene.removeItem(self.rasterList[i]["graphicsItem"])
        self.rasterList = []
        return   #short circuit
#      if (self.vectorPointsList != []):      
#        for i in xrange(len(self.vectorPointsList)):
#          self.scene.removeItem(self.vectorPointsList[i])
#        self.vectorPointsList = []
#      if (self.polyPointItems != []):      
      if (self.rasterPoly != None):      
        self.scene.removeItem(self.rasterPoly)
#        for i in xrange(len(self.polyPointItems)):
#          self.scene.removeItem(self.polyPointItems[i])
#        self.polyPointItems = []


    def getCurrentFOV(self):
      fov = {"x":0.0,"y":0.0}
      if (self.zoom2Radio.isChecked()):  #lowmagzoom      
        fov["x"] = daq_utils.lowMagFOVx/2.0
        fov["y"] = daq_utils.lowMagFOVy/2.0
      elif (self.zoom1Radio.isChecked()):
        fov["x"] = daq_utils.lowMagFOVx
        fov["y"] = daq_utils.lowMagFOVy
      elif (self.zoom4Radio.isChecked()):        
        fov["x"] = daq_utils.highMagFOVx/2.0
        fov["y"] = daq_utils.highMagFOVy/2.0
      else:
        fov["x"] = daq_utils.highMagFOVx
        fov["y"] = daq_utils.highMagFOVy
      return fov


    def screenXPixels2microns(self,pixels):
      fov = self.getCurrentFOV()
      fovX = fov["x"]
      return float(pixels)*(fovX/daq_utils.screenPixX)

    def screenYPixels2microns(self,pixels):
      fov = self.getCurrentFOV()
      fovY = fov["y"]
      return float(pixels)*(fovY/daq_utils.screenPixY)

    def screenXmicrons2pixels(self,microns):
      fov = self.getCurrentFOV()
      fovX = fov["x"]
      return int(round(microns*(daq_utils.screenPixX/fovX)))

    def screenYmicrons2pixels(self,microns):
      fov = self.getCurrentFOV()
      fovY = fov["y"]
      return int(round(microns*(daq_utils.screenPixY/fovY)))



    def definePolyRaster(self,raster_w,raster_h,stepsizeXPix,stepsizeYPix,point_x,point_y): #all come in as pixels, raster_w and raster_h are bounding box of drawn graphic
#raster status - 0=nothing done, 1=run, 2=displayed
      stepTime = float(self.exp_time_ledit.text())
      stepsize =float(self.rasterStepEdit.text())
      if ((stepsize/1000.0)/stepTime > 2.0):
        self.popupServerMessage("Stage speed exceeded. Increase exposure time, or decrease step size. Limit is 2mm/s.")
        self.eraseCB()        
        return
          
      beamWidth = float(self.beamWidth_ledit.text())
      beamHeight = float(self.beamHeight_ledit.text())
      rasterDef = {"rasterType":"normal","beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":self.sampx_pv.get(),"y":self.sampy_pv.get(),"z":self.sampz_pv.get(),"omega":self.omega_pv.get(),"stepsize":stepsize,"rowDefs":[]} #just storing step as microns, not using here      
      numsteps_h = int(raster_w/stepsizeXPix) #raster_w = width,goes to numsteps horizonatl
      numsteps_v = int(raster_h/stepsizeYPix)
      if (numsteps_h%2 == 0): # make odd numbers of rows and columns
        numsteps_h = numsteps_h + 1
      if (numsteps_v%2 == 0):
        numsteps_v = numsteps_v + 1
      point_offset_x = -(numsteps_h*stepsizeXPix)/2
      point_offset_y = -(numsteps_v*stepsizeYPix)/2
#      print "in define poly"
      if ((numsteps_h == 1) or (numsteps_v > numsteps_h and db_lib.getBeamlineConfigParam(daq_utils.beamline,"vertRasterOn"))): #vertical raster
        for i in xrange(numsteps_h):
          rowCellCount = 0
          for j in xrange(numsteps_v):
            newCellX = point_x+(i*stepsizeXPix)+point_offset_x
            newCellY = point_y+(j*stepsizeYPix)+point_offset_y
            if (1):
#            if (self.rasterPoly.contains(QtCore.QPointF(newCellX+(stepsizeXPix/2.0),newCellY+(stepsizeYPix/2.0)))): #stepping through every cell to see if it's in the bounding box                
              if (rowCellCount == 0): #start of a new row
                rowStartX = newCellX
                rowStartY = newCellY
              rowCellCount = rowCellCount+1
          if (rowCellCount != 0): #test for no points in this row of the bounding rect are in the poly?
            vectorStartX = self.screenXPixels2microns(rowStartX-self.centerMarker.x()-self.centerMarkerCharOffsetX)
            vectorEndX = vectorStartX 
            vectorStartY = self.screenYPixels2microns(rowStartY-self.centerMarker.y()-self.centerMarkerCharOffsetY)
            vectorEndY = vectorStartY + self.screenYPixels2microns(rowCellCount*stepsizeYPix)
            newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":rowCellCount}
            rasterDef["rowDefs"].append(newRowDef)
      else: #horizontal raster
        for i in xrange(numsteps_v):
          rowCellCount = 0
          for j in xrange(numsteps_h):
            newCellX = point_x+(j*stepsizeXPix)+point_offset_x
            newCellY = point_y+(i*stepsizeYPix)+point_offset_y
            if (1):
#            if (self.rasterPoly.contains(QtCore.QPointF(newCellX+(stepsizeXPix/2.0),newCellY+(stepsizeYPix/2.0)))): #stepping through every cell to see if it's in the bounding box                
              if (rowCellCount == 0): #start of a new row
                rowStartX = newCellX
                rowStartY = newCellY
              rowCellCount = rowCellCount+1
          if (rowCellCount != 0): #testing for no points in this row of the bounding rect are in the poly?
#            print("rowStartX =" + str(rowStartX))
            vectorStartX = self.screenXPixels2microns(rowStartX-self.centerMarker.x()-self.centerMarkerCharOffsetX)
#            print("vectorStartX = " + str(vectorStartX))
####            vectorEndX = vectorStartX + (rowCellCount*stepsize) #this is the correct definition, but the next one accounts for any scaling issues on the video image and looks better!!
            vectorEndX = vectorStartX + self.screenXPixels2microns(rowCellCount*stepsizeXPix) #this looks better
#            print("vectorEndX = " + str(vectorEndX))
            vectorStartY = self.screenYPixels2microns(rowStartY-self.centerMarker.y()-self.centerMarkerCharOffsetY)
            vectorEndY = vectorStartY
            newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":rowCellCount}
            rasterDef["rowDefs"].append(newRowDef)
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterDefaultWidth",float(self.osc_range_ledit.text()))
      db_lib.setBeamlineConfigParam(daq_utils.beamline,"rasterDefaultTime",float(self.exp_time_ledit.text()))
      
      self.addSampleRequestCB(rasterDef)
      return #short circuit


    def rasterIsDrawn(self,rasterReq):
      for i in xrange(len(self.rasterList)):
        if (self.rasterList[i] != None):
          if (self.rasterList[i]["uid"] == rasterReq["uid"]):
            return True
      return False
          


    def drawPolyRaster(self,rasterReq,x=-1,y=-1,z=-1): #rasterDef in microns,offset from center, need to convert to pixels to draw, mainly this is for displaying autoRasters, but also called in zoom change
      try:
        rasterDef = rasterReq["request_obj"]["rasterDef"]
      except KeyError:
        return
      beamSize = self.screenXmicrons2pixels(rasterDef["beamWidth"])
      stepsizeX = self.screenXmicrons2pixels(rasterDef["stepsize"])
      stepsizeY = self.screenYmicrons2pixels(rasterDef["stepsize"])      
      pen = QtGui.QPen(QtCore.Qt.green)
      if (0):
#      if (rasterDef["stepsize"]>20):                
        pen = QtGui.QPen(QtCore.Qt.green)
      else:
        pen = QtGui.QPen(QtCore.Qt.red)
#      pen = QtGui.QPen(QtCore.Qt.green)
##      pen.setStyle(QtCore.Qt.NoPen) #I think this is why we don't see the square!
      newRasterCellList = []
      try:
        if (rasterDef["rowDefs"][0]["start"]["y"] == rasterDef["rowDefs"][0]["end"]["y"]): #this is a horizontal raster
          rasterDir = "horizontal"
        else:
          rasterDir = "vertical"
      except IndexError:
        return
      for i in xrange(len(rasterDef["rowDefs"])):
        rowCellCount = 0
        for j in xrange(rasterDef["rowDefs"][i]["numsteps"]):
          if (rasterDir == "horizontal"):
            newCellX = self.screenXmicrons2pixels(rasterDef["rowDefs"][i]["start"]["x"])+(j*stepsizeX)+self.centerMarker.x()+self.centerMarkerCharOffsetX
            newCellY = self.screenYmicrons2pixels(rasterDef["rowDefs"][i]["start"]["y"])+self.centerMarker.y()+self.centerMarkerCharOffsetY
          else:
            newCellX = self.screenXmicrons2pixels(rasterDef["rowDefs"][i]["start"]["x"])+self.centerMarker.x()+self.centerMarkerCharOffsetX
            newCellY = self.screenYmicrons2pixels(rasterDef["rowDefs"][i]["start"]["y"])+(j*stepsizeY)+self.centerMarker.y()+self.centerMarkerCharOffsetY
#          print str(newCellX) + "  " + str(newCellY)
          if (rowCellCount == 0): #start of a new row
            rowStartX = newCellX
            rowStartY = newCellY
          newCell = rasterCell(newCellX,newCellY,stepsizeX, stepsizeY, self,self.scene)
          newRasterCellList.append(newCell)
##          newCellBeam = QtGui.QGraphicsEllipseItem(newCellX+((stepsize-beamSize)/2.0),newCellY+((stepsize-beamSize)/2.0),beamSize, beamSize, None,self.scene)
##          newRasterCellList.append(newCellBeam)
          newCell.setPen(pen)
#          newCellBeam.setPen(penBeam)
          rowCellCount = rowCellCount+1 #really just for test of new row
      newItemGroup = rasterGroup(self)
      self.scene.addItem(newItemGroup)
      for i in xrange(len(newRasterCellList)):
        newItemGroup.addToGroup(newRasterCellList[i])
#      if (x==-1):
#        newRasterGraphicsDesc = {"uid":rasterReq["uid"],"coords":{"x":self.sampx_pv.get(),"y":self.sampy_pv.get(),"z":self.sampz_pv.get()},"graphicsItem":newItemGroup}          
#      else:    
#        newRasterGraphicsDesc = {"uid":rasterReq["uid"],"coords":{"x":x,"y":y,"z":z},"graphicsItem":newItemGroup}
      newRasterGraphicsDesc = {"uid":rasterReq["uid"],"coords":{"x":rasterDef["x"],"y":rasterDef["y"],"z":rasterDef["z"],"omega":rasterDef["omega"]},"graphicsItem":newItemGroup}
      self.rasterList.append(newRasterGraphicsDesc)


    def reDrawPolyRasterObsolete(self,rasterReq,x,y,z): #rasterDef in microns,offset from center, need to convert to pixels to draw, mainly this is for displaying autoRasters, but also called in zoom change
      try:
        rasterDef = rasterReq["request_obj"]["rasterDef"]
      except KeyError:
        return
      beamSize = self.screenXmicrons2pixels(rasterDef["beamWidth"])
      stepsizeX = self.screenXmicrons2pixels(rasterDef["stepsize"])
      stepsizeY = self.screenYmicrons2pixels(rasterDef["stepsize"])      
      pen = QtGui.QPen(QtCore.Qt.green)
      if (rasterDef["stepsize"]>20):      
        pen = QtGui.QPen(QtCore.Qt.green)
      else:
        pen = QtGui.QPen(QtCore.Qt.red)
#      pen = QtGui.QPen(QtCore.Qt.green)
##      pen.setStyle(QtCore.Qt.NoPen) #I think this is why we don't see the square!
      newRasterCellList = []
      if (rasterDef["rowDefs"][0]["start"]["y"] == rasterDef["rowDefs"][0]["end"]["y"]): #this is a horizontal raster
        rasterDir = "horizontal"
      else:
        rasterDir = "vertical"          
      for i in xrange(len(rasterDef["rowDefs"])):
        rowCellCount = 0
        for j in xrange(rasterDef["rowDefs"][i]["numsteps"]):
          if (rasterDir == "horizontal"):
            newCellX = self.screenXmicrons2pixels(rasterDef["rowDefs"][i]["start"]["x"])+(j*stepsizeX)+self.centerMarker.x()+self.centerMarkerCharOffsetX
            newCellY = self.screenYmicrons2pixels(rasterDef["rowDefs"][i]["start"]["y"])+self.centerMarker.y()+self.centerMarkerCharOffsetY
          else:
            newCellX = self.screenXmicrons2pixels(rasterDef["rowDefs"][i]["start"]["x"])+self.centerMarker.x()+self.centerMarkerCharOffsetX
            newCellY = self.screenYmicrons2pixels(rasterDef["rowDefs"][i]["start"]["y"])+(j*stepsizeY)+self.centerMarker.y()+self.centerMarkerCharOffsetY
#          print str(newCellX) + "  " + str(newCellY)
          if (rowCellCount == 0): #start of a new row
            rowStartX = newCellX
            rowStartY = newCellY
          newCell = rasterCell(newCellX,newCellY,stepsizeX, stepsizeY, self,self.scene)
          newRasterCellList.append(newCell)
##          newCellBeam = QtGui.QGraphicsEllipseItem(newCellX+((stepsize-beamSize)/2.0),newCellY+((stepsize-beamSize)/2.0),beamSize, beamSize, None,self.scene)
##          newRasterCellList.append(newCellBeam)
          newCell.setPen(pen)
#          newCellBeam.setPen(penBeam)
          rowCellCount = rowCellCount+1 #really just for test of new row
      newItemGroup = rasterGroup(self)
      self.scene.addItem(newItemGroup)
      for i in xrange(len(newRasterCellList)):
        newItemGroup.addToGroup(newRasterCellList[i])
      newRasterGraphicsDesc = {"uid":rasterReq["uid"],"coords":{"x":x,"y":y,"z":z},"graphicsItem":newItemGroup}
      self.rasterList.append(newRasterGraphicsDesc)

      

#    def rasterItemMoveEvent(self, event): #crap?????
##      super(QtGui.QGraphicsRectItem, self).mouseMoveEvent(e)
#      print "caught move"
#      print self.rasterList[0]["graphicsItem"].pos()

#    def rasterItemReleaseEvent(self, event):
#      super(QtGui.QGraphicsRectItem, self).mouseReleaseEvent(e)
#      print "caught release"
#      print self.rasterList[0]["graphicsItem"].pos()


    def timerHutchRefresh(self):
#      print("timer hutch")
      try:
        file = cStringIO.StringIO(urllib.urlopen(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"hutchCornerCamURL"))).read())
        img = Image.open(file)
        qimage = ImageQt.ImageQt(img)
        pixmap_orig = QtGui.QPixmap.fromImage(qimage)
        self.pixmap_item_HutchCorner.setPixmap(pixmap_orig)        
      except:
        pass
      try:
        file = cStringIO.StringIO(urllib.urlopen(str(db_lib.getBeamlineConfigParam(daq_utils.beamline,"hutchTopCamURL"))).read())
        img = Image.open(file)
        qimage = ImageQt.ImageQt(img)
        pixmap_orig = QtGui.QPixmap.fromImage(qimage)
        self.pixmap_item_HutchTop.setPixmap(pixmap_orig)
      except:
        pass
      

    def timerEvent(self, event):
#      self.flushBuffer(self.capture)                  
      retval,self.readframe = self.capture.read()
      if self.readframe is None:
        return #maybe stop the timer also???
      self.currentFrame = cv2.cvtColor(self.readframe,cv2.COLOR_BGR2RGB)
      height,width=self.currentFrame.shape[:2]
      qimage=QtGui.QImage(self.currentFrame,width,height,3*width,QtGui.QImage.Format_RGB888)
#      print "got qimage" 
#      frameWidth = qimage.width()
#      frameHeight = qimage.height()
#      print(frameWidth)
#      print(frameHeight)
      pixmap_orig = QtGui.QPixmap.fromImage(qimage)
      if (0): 
#      if (frameWidth>1000): #for now, this can be more specific later if needed, but I really never want to scale here!! 3/16 - we eliminated the need for gui scaling.          
        pixmap = pixmap_orig.scaled(frameWidth/2,frameHeight/2)
        self.pixmap_item.setPixmap(pixmap)
      else:
#      print "got pixmap"
        self.pixmap_item.setPixmap(pixmap_orig)
#      print "done setting picture"


    def sceneKey(self, event):
        if (event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace):
          for i in xrange(len(self.rasterList)):
            if (self.rasterList[i] != None):
              if (self.rasterList[i]["graphicsItem"].isSelected()):
                try:
                  sceneReq = db_lib.getRequestByID(self.rasterList[i]["uid"])
                  if (sceneReq != None):
                    self.selectedSampleID = sceneReq["sample"]
                    db_lib.deleteRequest(sceneReq)["uid"]
                except AttributeError:
                  pass
                self.scene.removeItem(self.rasterList[i]["graphicsItem"])
                self.rasterList[i] = None
                self.treeChanged_pv.put(1)
          for i in xrange(len(self.centeringMarksList)):
            if (self.centeringMarksList[i] != None):
              if (self.centeringMarksList[i]["graphicsItem"].isSelected()):
                self.scene.removeItem(self.centeringMarksList[i]["graphicsItem"])        
                self.centeringMarksList[i] = None
          

    def pixelSelect(self, event):
        super(QtGui.QGraphicsPixmapItem, self.pixmap_item).mousePressEvent(event)
        x_click = float(event.pos().x())
        y_click = float(event.pos().y())
        penGreen = QtGui.QPen(QtCore.Qt.green)
        penRed = QtGui.QPen(QtCore.Qt.red)
        if (self.vidActionDefineCenterRadio.isChecked()):
          self.vidActionC2CRadio.setChecked(True) #because it's easy to forget defineCenter is on
          if (self.zoom4Radio.isChecked()): 
            comm_s = "changeImageCenterHighMag(" + str(x_click) + "," + str(y_click) + ",1)"
          elif (self.zoom3Radio.isChecked()):
            comm_s = "changeImageCenterHighMag(" + str(x_click) + "," + str(y_click) + ",0)"              
          if (self.zoom2Radio.isChecked()):        
            comm_s = "changeImageCenterLowMag(" + str(x_click) + "," + str(y_click) + ",1)"
          elif (self.zoom1Radio.isChecked()):
            comm_s = "changeImageCenterLowMag(" + str(x_click) + "," + str(y_click) + ",0)"              
          self.send_to_server(comm_s)
          return
        if (self.vidActionRasterDefRadio.isChecked()):
          self.click_positions.append(event.pos())
          self.polyPointItems.append(self.scene.addEllipse(x_click, y_click, 4, 4, penRed))
          if (len(self.click_positions) == 4):
            self.drawInteractiveRasterCB()
          return
        fov = self.getCurrentFOV()
        correctedC2C_x = daq_utils.screenPixCenterX + (x_click - (self.centerMarker.x()+self.centerMarkerCharOffsetX))
        correctedC2C_y = daq_utils.screenPixCenterY + (y_click - (self.centerMarker.y()+self.centerMarkerCharOffsetY))        
#        print(correctedC2C_x)
#        print(correctedC2C_y)        
        if (self.threeClickCount > 0): #3-click centering
          self.threeClickCount = self.threeClickCount + 1
          comm_s = 'center_on_click(' + str(correctedC2C_x) + "," + str(correctedC2C_y) + "," + str(fov["x"]) + "," + str(fov["y"]) + "," + '"screen",jog=90)'          
#          comm_s = 'center_on_click(' + str(x_click) + "," + str(y_click) + "," + str(fov["x"]) + "," + str(fov["y"]) + "," + '"screen",jog=90)'
        else:
          comm_s = 'center_on_click(' + str(correctedC2C_x) + "," + str(correctedC2C_y) + "," + str(fov["x"]) + "," + str(fov["y"])  + "," + '"screen",0)'
#          comm_s = 'center_on_click(' + str(x_click) + "," + str(y_click) + "," + str(fov["x"]) + "," + str(fov["y"])  + "," + '"screen",0)'
        if (not self.vidActionRasterExploreRadio.isChecked()):
#          if (self.pauseQueueButton.text() == "Continue"):
          if (1):              
            self.aux_send_to_server(comm_s)
          else:
            self.send_to_server(comm_s)          
        if (self.threeClickCount == 4):
          self.threeClickCount = 0
          self.click3Button.setStyleSheet("background-color: None")          
        return 


    def editScreenParamsCB(self):
      self.screenDefaultsDialog = screenDefaultsDialog()
#       self.w.setGeometry(QRect(100, 100, 400, 200))
      self.screenDefaultsDialog.show()


    def deleteFromQueueCBNOTUSED(self):
#      print "add to queue"
      selmod = self.dewarTree.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      i = 0
      item = self.dewarTree.model.itemFromIndex(indexes[i])
      db_lib.deleteRequest(self.selectedSampleRequest)["uid"]
      self.dewarTree.refreshTree()
#      item.setCheckState(Qt.Checked)

    def editSelectedRequestsCB(self):
      selmod = self.dewarTree.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      singleRequest = 1
      for i in xrange(len(indexes)):
        item = self.dewarTree.model.itemFromIndex(indexes[i])
        itemData = str(item.data(32).toString())
        itemDataType = str(item.data(33).toString())
        if (itemDataType == "request"): 
          self.selectedSampleRequest = db_lib.getRequestByID(itemData)
          self.editSampleRequestCB(singleRequest)
          singleRequest = 0
#            if (len(indexes)>1):
#            self.dataPathGB.setFilePrefix_ledit(str(self.selectedSampleRequest["file_prefix"]))
#          self.addSampleRequestCB(selectedSampleID=self.selectedSampleID)
#      self.refreshTree()
      self.treeChanged_pv.put(1)



    def editSampleRequestCB(self,singleRequest):
      colRequest=self.selectedSampleRequest
      reqObj = colRequest["request_obj"]
      reqObj["sweep_start"] = float(self.osc_start_ledit.text())
      reqObj["sweep_end"] = float(self.osc_end_ledit.text())+float(self.osc_start_ledit.text())
#      reqObj["sweep_end"] = float(self.osc_end_ledit.text())      
      reqObj["img_width"] = float(self.osc_range_ledit.text())
      reqObj["exposure_time"] = float(self.exp_time_ledit.text())
      reqObj["detDist"] = float(self.detDistMotorEntry.getEntry().text())      
      reqObj["resolution"] = float(self.resolution_ledit.text())
      if (singleRequest == 1): # a touch kludgy, but I want to be able to edit parameters for multiple requests w/o screwing the data loc info
        reqObj["file_prefix"] = str(self.dataPathGB.prefix_ledit.text())
        reqObj["basePath"] = str(self.dataPathGB.base_path_ledit.text())
        reqObj["directory"] = str(self.dataPathGB.dataPath_ledit.text())
        reqObj["file_number_start"] = int(self.dataPathGB.file_numstart_ledit.text())
#      colRequest["gridStep"] = self.rasterStepEdit.text()
#####      reqObj["attenuation"] = float(self.transmission_ledit.text())
      reqObj["slit_width"] = float(self.beamWidth_ledit.text())
      reqObj["slit_height"] = float(self.beamHeight_ledit.text())
      reqObj["energy"] = float(self.energy_ledit.text())
      wave = daq_utils.energy2wave(float(self.energy_ledit.text()))
      reqObj["wavelength"] = wave
      reqObj["fastDP"] =(self.fastDPCheckBox.isChecked() or self.fastEPCheckBox.isChecked() or self.dimpleCheckBox.isChecked())
      reqObj["fastEP"] =self.fastEPCheckBox.isChecked()
      reqObj["dimple"] =self.dimpleCheckBox.isChecked()      
      reqObj["xia2"] =self.xia2CheckBox.isChecked()
      reqObj["protocol"] = str(self.protoComboBox.currentText())
      if (reqObj["protocol"] == "vector" or reqObj["protocol"] == "stepVector"):
        reqObj["vectorParams"]["fpp"] = int(self.vectorFPP_ledit.text())
      colRequest["request_obj"] = reqObj
      db_lib.updateRequest(colRequest)
#      self.eraseCB()
      self.treeChanged_pv.put(1)
#      self.dewarTree.refreshTree()



    def addRequestsToAllSelectedCB(self):
      if (self.protoComboBox.currentText() == "raster" or self.protoComboBox.currentText() == "stepRaster"): #it confused people when they didn't need to add rasters explicitly
        return
      selmod = self.dewarTree.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      progressInc = 100.0/float(len(indexes))
#      self.progressDialog.setLabelText("Creating Requests")
      self.progressDialog.setWindowTitle("Creating Requests")
      self.progressDialog.show()
#      time.sleep(0.1)
      for i in xrange(len(indexes)):
        self.progressDialog.setValue(int((i+1)*progressInc))
        item = self.dewarTree.model.itemFromIndex(indexes[i])
        itemData = str(item.data(32).toString())
        itemDataType = str(item.data(33).toString())        
        if (itemDataType == "sample"): 
          self.selectedSampleID = itemData
        self.selectedSampleRequest = daq_utils.createDefaultRequest(self.selectedSampleID) #7/21/15  - not sure what this does, b/c I don't pass it, ahhh probably the commented line for prefix
        if (len(indexes)>1):
          self.dataPathGB.setFilePrefix_ledit(str(self.selectedSampleRequest["request_obj"]["file_prefix"]))
          self.dataPathGB.setDataPath_ledit(str(self.selectedSampleRequest["request_obj"]["directory"]))
          self.EScanDataPathGBTool.setFilePrefix_ledit(str(self.selectedSampleRequest["request_obj"]["file_prefix"]))
          self.EScanDataPathGBTool.setDataPath_ledit(str(self.selectedSampleRequest["request_obj"]["directory"]))
          self.EScanDataPathGB.setFilePrefix_ledit(str(self.selectedSampleRequest["request_obj"]["file_prefix"]))
          self.EScanDataPathGB.setDataPath_ledit(str(self.selectedSampleRequest["request_obj"]["directory"]))
        if (itemDataType != "container"):
          self.addSampleRequestCB(selectedSampleID=self.selectedSampleID)
#      self.refreshTree()
      self.progressDialog.close()
      self.treeChanged_pv.put(1)


    def addSampleRequestCB(self,rasterDef=None,selectedSampleID=None):
      if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"queueCollect") == 0):
        if (self.mountedPin_pv.get() != self.selectedSampleID):                    
          self.popupServerMessage("You can only add requests to a mounted sample, for now.")
          return
        
#skinner, not pretty below the way stuff is duplicated.
      if (float(self.osc_end_ledit.text()) < float(self.osc_range_ledit.text())):
        self.popupServerMessage("Osc range less than Osc width")
        return
      if (self.periodicTableTool.isVisible()): #this one is for periodicTableTool, the other block is periodicTable, 6/17 - we don't use tool anymore
        if (self.periodicTableTool.eltCurrent != None):
          symbol = self.periodicTableTool.eltCurrent.symbol
#          print(symbol)
#          print("EnergyScan1!!")        
          targetEdge = element_info[symbol][2]
          targetEnergy = ElementsInfo.Elements.Element[symbol]["binding"][targetEdge]
#          print(targetEnergy)
          colRequest = daq_utils.createDefaultRequest(self.selectedSampleID)
          sampleName = str(db_lib.getSampleNamebyID(colRequest["sample"]))
          runNum = db_lib.incrementSampleRequestCount(colRequest["sample"])
          (puckPosition,samplePositionInContainer,containerID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,colRequest["sample"])                
          reqObj = colRequest["request_obj"]
          reqObj["element"] = self.periodicTable.eltCurrent.symbol          
          reqObj["runNum"] = runNum
          reqObj["file_prefix"] = str(self.EScanDataPathGBTool.prefix_ledit.text())
          reqObj["basePath"] = str(self.EScanDataPathGBTool.base_path_ledit.text())
          reqObj["directory"] = str(self.EScanDataPathGBTool.base_path_ledit.text())+"/"+ str(daq_utils.getVisitName()) + "/"+sampleName+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"
#          reqObj["directory"] = str(self.EScanDataPathGBTool.base_path_ledit.text())+"/"+ str(daq_utils.getProposalID()) + "/"+sampleName+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"                    
          reqObj["file_number_start"] = int(self.EScanDataPathGBTool.file_numstart_ledit.text())
          reqObj["exposure_time"] = float(self.exp_time_ledit.text())          
          reqObj["protocol"] = "eScan"
          reqObj["scanEnergy"] = targetEnergy
          reqObj["runChooch"] = True #just hardcode for now
          reqObj["steps"] = int(self.escan_steps_ledit.text())          
          reqObj["stepsize"] = int(self.escan_stepsize_ledit.text())          
          colRequest["request_obj"] = reqObj             
          newSampleRequestID = db_lib.addRequesttoSample(self.selectedSampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=daq_utils.getProposalID())
#attempt here to select a newly created request.        
          self.SelectedItemData = newSampleRequestID
          newSampleRequest = db_lib.getRequestByID(newSampleRequestID)
          
          if (selectedSampleID == None): #this is a temp kludge to see if this is called from addAll
            self.treeChanged_pv.put(1)
        else:
          print("choose an element and try again")
        return          

      if (self.periodicTable.isVisible()):
        if (self.periodicTable.eltCurrent != None):
          symbol = self.periodicTable.eltCurrent.symbol
          targetEdge = element_info[symbol][2]
          if (daq_utils.beamline == "fmx"):                              
            mcaRoiLo = element_info[symbol][4]
            mcaRoiHi = element_info[symbol][5]
          else:
            mcaRoiLo = self.XRFInfoDict[symbol]-25
            mcaRoiHi = self.XRFInfoDict[symbol]+25
          targetEnergy = ElementsInfo.Elements.Element[symbol]["binding"][targetEdge]
#          print(targetEnergy)
          colRequest = daq_utils.createDefaultRequest(self.selectedSampleID)
          sampleName = str(db_lib.getSampleNamebyID(colRequest["sample"]))
          runNum = db_lib.incrementSampleRequestCount(colRequest["sample"])
          (puckPosition,samplePositionInContainer,containerID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,colRequest["sample"])                
          reqObj = colRequest["request_obj"]
          reqObj["element"] = self.periodicTable.eltCurrent.symbol
          reqObj["mcaRoiLo"] = mcaRoiLo
          reqObj["mcaRoiHi"] = mcaRoiHi
          reqObj["runNum"] = runNum
          reqObj["file_prefix"] = str(self.EScanDataPathGB.prefix_ledit.text())
          reqObj["basePath"] = str(self.EScanDataPathGB.base_path_ledit.text())
          reqObj["directory"] = str(self.EScanDataPathGB.base_path_ledit.text())+"/"+ str(daq_utils.getVisitName()) + "/"+sampleName+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"          
#          reqObj["directory"] = str(self.EScanDataPathGB.base_path_ledit.text())+"/"+ str(daq_utils.getProposalID()) + "/"+sampleName+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"          
          reqObj["file_number_start"] = int(self.EScanDataPathGB.file_numstart_ledit.text())
          reqObj["exposure_time"] = float(self.exp_time_ledit.text())                    
          reqObj["protocol"] = "eScan"
          reqObj["steps"] = int(self.escan_steps_ledit.text())          
          reqObj["stepsize"] = int(self.escan_stepsize_ledit.text())          
          
          reqObj["scanEnergy"] = targetEnergy
          reqObj["runChooch"] = True #just hardcode for now
          colRequest["request_obj"] = reqObj             
          newSampleRequestID = db_lib.addRequesttoSample(self.selectedSampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=daq_utils.getProposalID())
#attempt here to select a newly created request.        
          self.SelectedItemData = newSampleRequestID
          
          if (selectedSampleID == None): #this is a temp kludge to see if this is called from addAll
            self.treeChanged_pv.put(1)
        else:
          print("choose an element and try again")
        return          
            
#      self.selectedSampleID = self.selectedSampleRequest["sample_id"]

#      centeringOption = str(self.centeringComboBox.currentText())
#      if (centeringOption == "Interactive"):

# I don't like the code duplication, but one case is the mounted sample and selected centerings - so it's in a loop for multiple reqs, the other requires autocenter.
      if ((self.mountedPin_pv.get() == self.selectedSampleID) and (len(self.centeringMarksList) != 0)): 
        selectedCenteringFound = 0
        for i in xrange(len(self.centeringMarksList)):
           if (self.centeringMarksList[i]["graphicsItem"].isSelected()):
             selectedCenteringFound = 1
             colRequest = daq_utils.createDefaultRequest(self.selectedSampleID)
             sampleName = str(db_lib.getSampleNamebyID(colRequest["sample"]))
             runNum = db_lib.incrementSampleRequestCount(colRequest["sample"])
             (puckPosition,samplePositionInContainer,containerID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,colRequest["sample"])                   
             reqObj = colRequest["request_obj"]
             reqObj["runNum"] = runNum
             reqObj["sweep_start"] = float(self.osc_start_ledit.text())
             reqObj["sweep_end"] = float(self.osc_end_ledit.text())+float(self.osc_start_ledit.text())
#             reqObj["sweep_end"] = float(self.osc_end_ledit.text())             
             reqObj["img_width"] = float(self.osc_range_ledit.text())
             db_lib.setBeamlineConfigParam(daq_utils.beamline,"screen_default_width",float(self.osc_range_ledit.text()))
             db_lib.setBeamlineConfigParam(daq_utils.beamline,"screen_default_time",float(self.exp_time_ledit.text()))
             reqObj["exposure_time"] = float(self.exp_time_ledit.text())
             reqObj["resolution"] = float(self.resolution_ledit.text())
             reqObj["file_prefix"] = str(self.dataPathGB.prefix_ledit.text()+"_C"+str(i+1))

#             reqObj["directory"] = str(self.dataPathGB.dataPath_ledit.text())
             reqObj["basePath"] = str(self.dataPathGB.base_path_ledit.text())
             reqObj["directory"] = str(self.dataPathGB.base_path_ledit.text())+"/"+ str(daq_utils.getVisitName()) + "/"+sampleName+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"             
#             reqObj["directory"] = str(self.dataPathGB.base_path_ledit.text())+"/"+ str(daq_utils.getProposalID()) + "/"+sampleName+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"             
             reqObj["file_number_start"] = int(self.dataPathGB.file_numstart_ledit.text())
#             colRequest["gridStep"] = self.rasterStepEdit.text()
######             reqObj["attenuation"] = float(self.transmission_ledit.text())
             reqObj["slit_width"] = float(self.beamWidth_ledit.text())
             reqObj["slit_height"] = float(self.beamHeight_ledit.text())
             reqObj["energy"] = float(self.energy_ledit.text())             
             wave = daq_utils.energy2wave(float(self.energy_ledit.text()))
             reqObj["wavelength"] = wave
             reqObj["detDist"] = float(self.detDistMotorEntry.getEntry().text())             
             reqObj["protocol"] = str(self.protoComboBox.currentText())
             reqObj["pos_x"] = float(self.centeringMarksList[i]["sampCoords"]["x"])
             reqObj["pos_y"] = float(self.centeringMarksList[i]["sampCoords"]["y"])
             reqObj["pos_z"] = float(self.centeringMarksList[i]["sampCoords"]["z"])
             reqObj["fastDP"] = (self.fastDPCheckBox.isChecked() or self.fastEPCheckBox.isChecked() or self.dimpleCheckBox.isChecked())
             reqObj["fastEP"] =self.fastEPCheckBox.isChecked()
             reqObj["dimple"] =self.dimpleCheckBox.isChecked()             
             reqObj["xia2"] =self.xia2CheckBox.isChecked()
             if (reqObj["protocol"] == "characterize" or reqObj["protocol"] == "ednaCol"):
               characterizationParams = {"aimed_completeness":float(self.characterizeCompletenessEdit.text()),"aimed_multiplicity":str(self.characterizeMultiplicityEdit.text()),"aimed_resolution":float(self.characterizeResoEdit.text()),"aimed_ISig":float(self.characterizeISIGEdit.text())}
               reqObj["characterizationParams"] = characterizationParams
             colRequest["request_obj"] = reqObj             
             newSampleRequestID = db_lib.addRequesttoSample(self.selectedSampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=daq_utils.getProposalID())
#attempt here to select a newly created request.        
             self.SelectedItemData = newSampleRequestID
             
#             db_lib.updateRequest(colRequest)
#             time.sleep(1) #for now only because I use timestamp for sample creation!!!!!
        if (selectedCenteringFound == 0):
          message = QtGui.QErrorMessage(self)
          message.setModal(True)
          message.showMessage("You need to select a centering.")
      else: #autocenter or interactive
        colRequest=self.selectedSampleRequest
        sampleName = str(db_lib.getSampleNamebyID(colRequest["sample"]))
        (puckPosition,samplePositionInContainer,containerID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,colRequest["sample"])              
        runNum = db_lib.incrementSampleRequestCount(colRequest["sample"])
        reqObj = colRequest["request_obj"]
        centeringOption = str(self.centeringComboBox.currentText())
        reqObj["centeringOption"] = centeringOption        
        if ((centeringOption == "Interactive" and self.mountedPin_pv.get() == self.selectedSampleID) or centeringOption == "Testing"): #user centered manually
          reqObj["pos_x"] = float(self.sampx_pv.get())
          reqObj["pos_y"] = float(self.sampy_pv.get())
          reqObj["pos_z"] = float(self.sampz_pv.get())
        reqObj["runNum"] = runNum
        reqObj["sweep_start"] = float(self.osc_start_ledit.text())
#        reqObj["sweep_end"] = float(self.osc_end_ledit.text())
        reqObj["sweep_end"] = float(self.osc_end_ledit.text())+float(self.osc_start_ledit.text())
        reqObj["img_width"] = float(self.osc_range_ledit.text())
        reqObj["exposure_time"] = float(self.exp_time_ledit.text())
        if (rasterDef == None):        
          db_lib.setBeamlineConfigParam(daq_utils.beamline,"screen_default_width",float(self.osc_range_ledit.text()))
          db_lib.setBeamlineConfigParam(daq_utils.beamline,"screen_default_time",float(self.exp_time_ledit.text()))
        reqObj["resolution"] = float(self.resolution_ledit.text())
        reqObj["directory"] = str(self.dataPathGB.base_path_ledit.text())+ "/" + str(daq_utils.getVisitName()) + "/" +str(self.dataPathGB.prefix_ledit.text())+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"
#        reqObj["directory"] = str(self.dataPathGB.base_path_ledit.text())+ "/" + str(daq_utils.getProposalID()) + "/" +str(self.dataPathGB.prefix_ledit.text())+"/" + str(runNum) + "/"+db_lib.getContainerNameByID(containerID)+"_"+str(samplePositionInContainer+1)+"/"
        reqObj["basePath"] = str(self.dataPathGB.base_path_ledit.text())
        reqObj["file_prefix"] = str(self.dataPathGB.prefix_ledit.text())
        reqObj["file_number_start"] = int(self.dataPathGB.file_numstart_ledit.text())
        if (abs(reqObj["sweep_end"]-reqObj["sweep_start"])<10.0):
          reqObj["fastDP"] = False
          reqObj["fastEP"] = False
          reqObj["dimple"] = False          
        else:
          reqObj["fastDP"] = (self.fastDPCheckBox.isChecked() or self.fastEPCheckBox.isChecked() or self.dimpleCheckBox.isChecked())
          reqObj["fastEP"] =self.fastEPCheckBox.isChecked()
          reqObj["dimple"] =self.dimpleCheckBox.isChecked()          
        reqObj["xia2"] =self.xia2CheckBox.isChecked()
#        colRequest["gridStep"] = self.rasterStepEdit.text()
#######        reqObj["attenuation"] = float(self.transmission_ledit.text())
        reqObj["slit_width"] = float(self.beamWidth_ledit.text())
        reqObj["slit_height"] = float(self.beamHeight_ledit.text())
        reqObj["energy"] = float(self.energy_ledit.text())                  
        try:        
          wave = daq_utils.energy2wave(float(self.energy_ledit.text()))
        except ValueError:
          wave = 1.1

        reqObj["wavelength"] = wave
        reqObj["protocol"] = str(self.protoComboBox.currentText())
        try:
          reqObj["detDist"] = float(self.detDistMotorEntry.getEntry().text())
        except ValueError:
          reqObj["detDist"] = 500.0
#        print colRequest
#        if (rasterDef != False):
        if (reqObj["protocol"] == "multiCol" or reqObj["protocol"] == "multiColQ"):
          reqObj["gridStep"] = float(self.rasterStepEdit.text())
          reqObj["diffCutoff"] = float(self.multiColCutoffEdit.text())                      
        if (rasterDef != None):
          reqObj["rasterDef"] = rasterDef
          reqObj["gridStep"] = float(self.rasterStepEdit.text())
        if (reqObj["protocol"] == "characterize" or reqObj["protocol"] == "ednaCol"):
          characterizationParams = {"aimed_completeness":float(self.characterizeCompletenessEdit.text()),"aimed_multiplicity":str(self.characterizeMultiplicityEdit.text()),"aimed_resolution":float(self.characterizeResoEdit.text()),"aimed_ISig":float(self.characterizeISIGEdit.text())}
          reqObj["characterizationParams"] = characterizationParams
        if (reqObj["protocol"] == "vector" or reqObj["protocol"] == "stepVector"):
          if (0):
#          if (float(self.osc_end_ledit.text()) < 5.0):              
            self.popupServerMessage("Vector oscillation must be at least 5.0 degrees.")
            return
          if (centeringOption == "Interactive"):                    
            selectedCenteringFound = 1            
            x_vec_end = self.vectorEnd["coords"]["x"]
            y_vec_end = self.vectorEnd["coords"]["y"]
            z_vec_end = self.vectorEnd["coords"]["z"]
            x_vec_start = self.vectorStart["coords"]["x"]
            y_vec_start = self.vectorStart["coords"]["y"]
            z_vec_start = self.vectorStart["coords"]["z"]
            x_vec = x_vec_end - x_vec_start
            y_vec = y_vec_end - y_vec_start
            z_vec = z_vec_end - z_vec_start
            trans_total = math.sqrt(x_vec**2 + y_vec**2 + z_vec**2)
#          print trans_total
            framesPerPoint = int(self.vectorFPP_ledit.text())
            vectorParams={"vecStart":self.vectorStart["coords"],"vecEnd":self.vectorEnd["coords"],"x_vec":x_vec,"y_vec":y_vec,"z_vec":z_vec,"trans_total":trans_total,"fpp":framesPerPoint}
            reqObj["vectorParams"] = vectorParams
        colRequest["request_obj"] = reqObj
        newSampleRequestID = db_lib.addRequesttoSample(self.selectedSampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=daq_utils.getProposalID())
#attempt here to select a newly created request.        
        self.SelectedItemData = newSampleRequestID
        newSampleRequest = db_lib.getRequestByID(newSampleRequestID)
        
#        if (rasterDef != False):
        if (rasterDef != None):
          self.rasterDefList.append(newSampleRequest)
          self.drawPolyRaster(newSampleRequest)
#        db_lib.updateRequest(colRequest)
#      self.eraseCB()
      if (selectedSampleID == None): #this is a temp kludge to see if this is called from addAll
        self.treeChanged_pv.put(1)
#      self.dewarTree.refreshTree()


    def cloneRequestCB(self):
      self.eraseCB()
      colRequest=self.selectedSampleRequest
      reqObj = colRequest["request_obj"]
      rasterDef = reqObj["rasterDef"]
      self.addSampleRequestCB(rasterDef)      
###      newSampleRequestID = db_lib.addRequesttoSample(self.selectedSampleID,reqObj["protocol"],daq_utils.owner,reqObj,priority=5000,proposalID=daq_utils.getProposalID())
#      self.SelectedItemData = newSampleRequestID      
###      self.treeChanged_pv.put(1)            

    def collectQueueCB(self):
      currentRequest = db_lib.popNextRequest(daq_utils.beamline)
      if (currentRequest == {}):
        self.addRequestsToAllSelectedCB()        
      print "running queue"
      self.send_to_server("runDCQueue()")

    def warmupGripperCB(self):
      self.send_to_server("warmupGripper()")      


    def removePuckCB(self):
      dewarPos, ok = DewarDialog.getDewarPos(parent=self,action="remove")
#      ipos = int(dewarPos)
#      ipos = int(dewarPos)-1
#      print ipos
#      if (ok):
##      if (1):
#        db_lib.removePuckFromDewar(ipos)
##        self.treeChanged_pv.put(1)
##        self.dewarTree.refreshTree()

    def setVectorStartCB(self): #save sample x,y,z
#      print "set vector start"
      if (self.vectorStart != None):
        self.scene.removeItem(self.vectorStart["graphicsitem"])
        self.vectorStart = None
      
      pen = QtGui.QPen(QtCore.Qt.blue)
      brush = QtGui.QBrush(QtCore.Qt.blue)
      markWidth = 10      
      vecStartMarker = self.scene.addEllipse(self.centerMarker.x()-(markWidth/2.0)-1+self.centerMarkerCharOffsetX,self.centerMarker.y()-(markWidth/2.0)-1+self.centerMarkerCharOffsetY,markWidth,markWidth,pen,brush)
#      vecStartMarker = self.scene.addEllipse(daq_utils.screenPixCenterX-5,daq_utils.screenPixCenterY-5,10, 10, pen,brush)            
      vectorStartcoords = {"x":self.sampx_pv.get(),"y":self.sampy_pv.get(),"z":self.sampz_pv.get()}
      self.vectorStart = {"coords":vectorStartcoords,"graphicsitem":vecStartMarker,"centerCursorX":self.centerMarker.x(),"centerCursorY":self.centerMarker.y()}
######      self.send_to_server("set_vector_start()")
#      print self.vectorStartcoords
#      self.vectorStartFlag = 1


    def setVectorEndCB(self): #save sample x,y,z
      if (self.vectorEnd != None):
        self.scene.removeItem(self.vectorEnd["graphicsitem"])
        self.scene.removeItem(self.vecLine)
        self.vectorEnd = None
        
#      print "set vector end"        
      pen = QtGui.QPen(QtCore.Qt.blue)
      brush = QtGui.QBrush(QtCore.Qt.blue)
      markWidth = 10            
      vecEndMarker = self.scene.addEllipse(self.centerMarker.x()-(markWidth/2.0)-1+self.centerMarkerCharOffsetX,self.centerMarker.y()-(markWidth/2.0)-1+self.centerMarkerCharOffsetY,markWidth,markWidth,pen,brush)
#      vecEndMarker = self.scene.addEllipse(daq_utils.screenPixCenterX-5,daq_utils.screenPixCenterY-5,10, 10, pen,brush)            
      vectorEndcoords = {"x":self.sampx_pv.get(),"y":self.sampy_pv.get(),"z":self.sampz_pv.get()}
      self.vectorEnd = {"coords":vectorEndcoords,"graphicsitem":vecEndMarker,"centerCursorX":self.centerMarker.x(),"centerCursorY":self.centerMarker.y()}
      self.vecLine = self.scene.addLine(self.centerMarker.x()+self.vectorStart["graphicsitem"].x()+self.centerMarkerCharOffsetX,self.centerMarker.y()+self.vectorStart["graphicsitem"].y()+self.centerMarkerCharOffsetY,self.centerMarker.x()+vecEndMarker.x()+self.centerMarkerCharOffsetX,self.centerMarker.y()+vecEndMarker.y()+self.centerMarkerCharOffsetY, pen)
#      self.vecLine = self.scene.addLine(daq_utils.screenPixCenterX+self.vectorStart["graphicsitem"].x(),daq_utils.screenPixCenterY+self.vectorStart["graphicsitem"].y(),daq_utils.screenPixCenterX+vecEndMarker.x(),daq_utils.screenPixCenterY+vecEndMarker.y(), pen)      
      self.vecLine.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
#####      self.send_to_server("set_vector_end()")
#      self.vecLine = self.scene.addLine(self.vecStartMarker.scenePos().x(),self.vecStartMarker.scenePos().y(),self.vecEndMarker.scenePos().x(),self.vecEndMarker.scenePos().y(), pen)

    def clearVectorCB(self):
      if (self.vectorStart != None):
        self.scene.removeItem(self.vectorStart["graphicsitem"])
        self.vectorStart = None
      if (self.vectorEnd != None):
        self.scene.removeItem(self.vectorEnd["graphicsitem"])
        self.scene.removeItem(self.vecLine)
        self.vectorEnd = None

    def puckToDewarCB(self):
       puckName, ok = PuckDialog.getPuckName()
#       print puckName
       if (ok):
         dewarPos, ok = DewarDialog.getDewarPos(parent=self,action="add")
         ipos = int(dewarPos)+1
#         ipos = int(dewarPos)-1
         if (ok):
           db_lib.insertIntoContainer(daq_utils.primaryDewarName,daq_utils.beamline,ipos,db_lib.getContainerIDbyName(puckName,daq_utils.owner))
           self.treeChanged_pv.put(1)


    def stopRunCB(self):
      print "stopping collection"
      self.aux_send_to_server("stopDCQueue(1)")

    def stopQueueCB(self):
      print "stopping queue"
      if (self.pauseQueueButton.text() == "Continue"):
        self.aux_send_to_server("continue_data_collection()")        
      else:
        self.aux_send_to_server("stopDCQueue(2)")

    def mountSampleCB(self):
      if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"mountEnabled") == 0):
        self.popupServerMessage("Mounting disabled!! Call staff!")
        return
      print "mount selected sample"
      self.eraseCB()      
      self.selectedSampleID = self.selectedSampleRequest["sample"]
      self.send_to_server("mountSample(\""+str(self.selectedSampleID)+"\")")
      self.zoom1Radio.setChecked(True)      
      self.zoomLevelToggledCB("Zoom1")
      self.protoComboBox.setCurrentIndex(self.protoComboBox.findText(str("standard")))
      self.protoComboActivatedCB("standard")
###      self.showProtParams()

    def unmountSampleCB(self):
      print "unmount sample"
      self.eraseCB()      
      self.send_to_server("unmountSample()")


    def refreshCollectionParams(self,selectedSampleRequest):
      reqObj = selectedSampleRequest["request_obj"]
      self.protoComboBox.setCurrentIndex(self.protoComboBox.findText(str(reqObj["protocol"])))
      protocol = str(reqObj["protocol"])
      if (protocol == "raster"):
        self.protoRasterRadio.setChecked(True)
      elif (protocol == "standard"):
        self.protoStandardRadio.setChecked(True)
      elif (protocol == "vector"):
        self.protoVectorRadio.setChecked(True)
      else:
        self.protoOtherRadio.setChecked(True)
      
      self.osc_start_ledit.setText(str(reqObj["sweep_start"]))
      self.osc_end_ledit.setText(str(reqObj["sweep_end"]-reqObj["sweep_start"]))
#      self.osc_end_ledit.setText(str(reqObj["sweep_end"]))      
      self.osc_range_ledit.setText(str(reqObj["img_width"]))
      self.exp_time_ledit.setText(str(reqObj["exposure_time"]))
      self.resolution_ledit.setText(str(reqObj["resolution"]))
      self.dataPathGB.setFileNumstart_ledit(str(reqObj["file_number_start"]))
      self.beamWidth_ledit.setText(str(reqObj["slit_width"]))
      self.beamHeight_ledit.setText(str(reqObj["slit_height"]))
      if (reqObj.has_key("fastDP")):
        self.fastDPCheckBox.setChecked((reqObj["fastDP"] or reqObj["fastEP"] or reqObj["dimple"]))
      if (reqObj.has_key("fastEP")):
        self.fastEPCheckBox.setChecked(reqObj["fastEP"])
      if (reqObj.has_key("dimple")):
        self.dimpleCheckBox.setChecked(reqObj["dimple"])        
      if (reqObj.has_key("xia2")):
        self.xia2CheckBox.setChecked(reqObj["xia2"])
      reqObj["energy"] = float(self.energy_ledit.text())
      self.energy_ledit.setText(str(reqObj["energy"]))                        
      energy_s = str(daq_utils.wave2energy(reqObj["wavelength"]))
#      energy_s = "%.4f" % (12.3985/selectedSampleRequest["wavelength"])
##      self.energy_ledit.setText(str(energy_s))
########      self.transmission_ledit.setText(str(reqObj["attenuation"]))
      dist_s = str(reqObj["detDist"])
#      dist_s = "%.2f" % (daq_utils.distance_from_reso(daq_utils.det_radius,reqObj["resolution"],reqObj["wavelength"],0))      
      self.detDistMotorEntry.getEntry().setText(str(dist_s))
      self.dataPathGB.setFilePrefix_ledit(str(reqObj["file_prefix"]))
      self.dataPathGB.setBasePath_ledit(str(reqObj["basePath"]))
      self.dataPathGB.setDataPath_ledit(str(reqObj["directory"]))
      if (str(reqObj["protocol"]) == "characterize" or str(reqObj["protocol"]) == "ednaCol"): 
        prefix_long = str(reqObj["directory"])+"/ref-"+str(reqObj["file_prefix"])
      else:
        prefix_long = str(reqObj["directory"])+"/"+str(reqObj["file_prefix"])
      fnumstart=reqObj["file_number_start"]

      if (str(reqObj["protocol"]) == "characterize" or str(reqObj["protocol"]) == "ednaCol" or str(reqObj["protocol"]) == "standard" or str(reqObj["protocol"]) == "vector"):
#      if (str(reqObj["protocol"]) == "characterize" or str(reqObj["protocol"]) == "ednaCol" or str(reqObj["protocol"]) == "standard"):                    
        if (selectedSampleRequest.has_key("priority")):
          if (selectedSampleRequest["priority"] < 0 and self.albulaDispCheckBox.isChecked()):
            firstFilename = daq_utils.create_filename(prefix_long,fnumstart)            
#            albulaUtils.albulaDisp(firstFilename)
            albulaUtils.albulaDispFile(firstFilename)            
      self.rasterStepEdit.setText(str(reqObj["gridStep"]))
      if (reqObj["gridStep"] == self.rasterStepDefs["Coarse"]):
        self.rasterGrainCoarseRadio.setChecked(True)
      elif (reqObj["gridStep"] == self.rasterStepDefs["Fine"]):
        self.rasterGrainFineRadio.setChecked(True)
      elif (reqObj["gridStep"] == self.rasterStepDefs["VFine"]):
        self.rasterGrainVFineRadio.setChecked(True)
      else:
        self.rasterGrainCustomRadio.setChecked(True)          
      rasterStep = int(reqObj["gridStep"])
#      self.eraseCB()
      if (str(reqObj["protocol"])== "raster" or str(reqObj["protocol"])== "stepRaster"):
        if (not self.rasterIsDrawn(selectedSampleRequest)):
#        if (1):            
          self.drawPolyRaster(selectedSampleRequest)
          self.fillPolyRaster(selectedSampleRequest,takeSnapshot=False)
        self.processSampMove(self.sampx_pv.get(),"x")
        self.processSampMove(self.sampy_pv.get(),"y")
        self.processSampMove(self.sampz_pv.get(),"z")
        if (abs(selectedSampleRequest["request_obj"]["rasterDef"]["omega"]-self.omega_pv.get()) > 5.0):
          comm_s = "mvaDescriptor(\"omega\"," + str(selectedSampleRequest["request_obj"]["rasterDef"]["omega"]) + ")"
          self.send_to_server(comm_s)
      if (str(reqObj["protocol"])== "eScan"):
        try:
          self.escan_steps_ledit.setText(str(reqObj["steps"]))
          self.escan_stepsize_ledit.setText(str(reqObj["stepsize"]))
          self.EScanDataPathGB.setBasePath_ledit(reqObj["basePath"])
          self.EScanDataPathGB.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGB.setFileNumstart_ledit(str(reqObj["file_number_start"]))          
          self.EScanDataPathGB.setFilePrefix_ledit(str(reqObj["file_prefix"]))                  
          self.periodicTable.elementClicked(reqObj["element"])
        except KeyError:        
          pass
      elif (str(reqObj["protocol"])== "characterize" or str(reqObj["protocol"])== "ednaCol"):
        characterizationParams = reqObj["characterizationParams"]
        self.characterizeCompletenessEdit.setText(str(characterizationParams["aimed_completeness"]))
        self.characterizeISIGEdit.setText(str(characterizationParams["aimed_ISig"]))
        self.characterizeResoEdit.setText(str(characterizationParams["aimed_resolution"]))
        self.characterizeMultiplicityEdit.setText(str(characterizationParams["aimed_multiplicity"]))
      else: #for now, erase the rasters if a non-raster is selected, need to rationalize later
#        self.eraseDisplayCB()
        pass
      self.showProtParams()
      



    def row_clicked(self,index): #I need "index" here? seems like I get it from selmod, but sometimes is passed
      selmod = self.dewarTree.selectionModel()
      selection = selmod.selection()
      indexes = selection.indexes()
      if (len(indexes)==0):
        return
#      for i in xrange(len(indexes)):
      i = 0
      item = self.dewarTree.model.itemFromIndex(indexes[i])

#      sample_name = indexes[i].data().toString()
#      print sample_name
      parent = indexes[i].parent()
      puck_name = parent.data().toString()
#      print puck_name
#      sampleRequest = self.dewarTree.sampleRequests[item.data().toInt()[0]]
      itemData = str(item.data(32).toString())
#      print itemData
      itemDataType = str(item.data(33).toString())
#      print itemDataType
      
      self.SelectedItemData = itemData # an attempt to know what is selected and preserve it when refreshing the tree
#      sample_name = getSampleIdFromDewarPos(itemData)

      if (itemData == ""):
        print "nothing there"
        return
      elif (itemDataType == "container"):
        print "I'm a puck"
        return
      elif (itemDataType == "sample"):
        self.selectedSampleID = itemData
        sample = db_lib.getSampleByID(self.selectedSampleID)
        owner = sample["owner"]
#        if (owner != daq_utils.owner):
#          return
        sample_name = db_lib.getSampleNamebyID(self.selectedSampleID)
        print "sample in pos " + str(itemData) 
        if (self.osc_start_ledit.text() == ""):
          self.selectedSampleRequest = daq_utils.createDefaultRequest(itemData)
          self.refreshCollectionParams(self.selectedSampleRequest)
          reqObj = self.selectedSampleRequest["request_obj"]
          self.dataPathGB.setFilePrefix_ledit(str(reqObj["file_prefix"]))          
          self.dataPathGB.setBasePath_ledit(reqObj["basePath"])
          self.dataPathGB.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGBTool.setFilePrefix_ledit(str(reqObj["file_prefix"]))          
          self.EScanDataPathGBTool.setBasePath_ledit(reqObj["basePath"])
          self.EScanDataPathGBTool.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGBTool.setFileNumstart_ledit(str(reqObj["file_number_start"]))          
          self.EScanDataPathGB.setFilePrefix_ledit(str(reqObj["file_prefix"]))          
          self.EScanDataPathGB.setBasePath_ledit(reqObj["basePath"])
          self.EScanDataPathGB.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGB.setFileNumstart_ledit(str(reqObj["file_number_start"]))          
          
          if (self.vidActionRasterDefRadio.isChecked()):
#          self.selectedSampleRequest["protocol"] = "raster"
            self.protoComboBox.setCurrentIndex(self.protoComboBox.findText(str("raster")))
            self.showProtParams()
        elif (str(self.protoComboBox.currentText()) == "screen"):
          self.selectedSampleRequest = daq_utils.createDefaultRequest(itemData)
          self.refreshCollectionParams(self.selectedSampleRequest)

        else:
          self.selectedSampleRequest = daq_utils.createDefaultRequest(itemData)
          reqObj = self.selectedSampleRequest["request_obj"]
          self.dataPathGB.setFilePrefix_ledit(str(reqObj["file_prefix"]))          
          self.dataPathGB.setBasePath_ledit(reqObj["basePath"])
          self.dataPathGB.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGBTool.setFilePrefix_ledit(str(reqObj["file_prefix"]))          
          self.EScanDataPathGBTool.setBasePath_ledit(reqObj["basePath"])
          self.EScanDataPathGBTool.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGBTool.setFileNumstart_ledit(str(reqObj["file_number_start"]))          
          self.EScanDataPathGB.setFilePrefix_ledit(str(reqObj["file_prefix"]))          
          self.EScanDataPathGB.setBasePath_ledit(reqObj["basePath"])
          self.EScanDataPathGB.setDataPath_ledit(reqObj["directory"])
          self.EScanDataPathGB.setFileNumstart_ledit(str(reqObj["file_number_start"]))          
          
      else: #request
        self.selectedSampleRequest = db_lib.getRequestByID(itemData)
        reqObj = self.selectedSampleRequest["request_obj"]
        reqID = self.selectedSampleRequest["uid"]
        self.selectedSampleID = self.selectedSampleRequest["sample"]        
        sample = db_lib.getSampleByID(self.selectedSampleID)
        owner = sample["owner"]
#        if (owner != daq_utils.owner):
#          return
        if (reqObj["protocol"] == "eScan"):
          if (reqObj["runChooch"]):
            resultList = db_lib.getResultsforRequest(reqID)
            if (len(resultList) > 0):
              lastResult = resultList[-1]
#              if (lastResult["result_type"] == "choochResult"): #I don't know how to get this from the damn DBRef type, see next line, not ideal, but not bad.
#              if (db_lib.getResult(lastResult['uid'], as_mongo_obj=True).result_type.name == "choochResult"):
              if (db_lib.getResult(lastResult['uid'])["result_type"] == "choochResult"):                  
                resultID = lastResult['uid']
                print("plotting chooch")
                self.processChoochResult(resultID)

#        if (self.selectedSampleRequest["protocol"] == "raster"): #might want this, problem is that it requires "rasterSelect", and maybe we don't want that.
#          for i in xrange(len(self.rasterList)):
#            if (self.rasterList[i] != None):
#              if (self.rasterList[i]["request_id"] == self.selectedSampleRequest["request_id"]):
#                self.rasterList[i]["graphicsItem"].setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)            
#                self.rasterList[i]["graphicsItem"].setSelected(True)
#              else:
#                self.rasterList[i]["graphicsItem"].setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)            
#                self.rasterList[i]["graphicsItem"].setSelected(False)

#####        self.eraseDisplayCB()
        self.refreshCollectionParams(self.selectedSampleRequest)

#      self.dewarTree.refreshTree()
##      numimages = (sampleRequest["sweep_end"] - sampleRequest["sweep_start"])/sampleRequest["img_width"]
##      self.dcFrame.num_images_ledit.setText(str(numimages))


    def processXrecRasterCB(self,value=None, char_value=None, **kw):
      xrecFlag = value
      if (xrecFlag != "0"):
        self.emit(QtCore.SIGNAL("xrecRasterSignal"),xrecFlag)

    def processChoochResultsCB(self,value=None, char_value=None, **kw):
      choochFlag = value
      if (choochFlag != "0"):
        self.emit(QtCore.SIGNAL("choochResultSignal"),choochFlag)

    def mountedPinChangedCB(self,value=None, char_value=None, **kw):
      mountedPinPos = value
      self.emit(QtCore.SIGNAL("mountedPinSignal"),mountedPinPos)

    def controlMasterChangedCB(self,value=None, char_value=None, **kw):
      controlMasterPID = value
      self.emit(QtCore.SIGNAL("controlMasterSignal"),controlMasterPID)
      
    def shutterChangedCB(self,value=None, char_value=None, **kw):
      shutterVal = value        
      self.emit(QtCore.SIGNAL("fastShutterSignal"),shutterVal)
      
    def processSampMoveCB(self,value=None, char_value=None, **kw):
      posRBV = value
      motID = kw["motID"]
      self.emit(QtCore.SIGNAL("sampMoveSignal"),posRBV,motID)

    def processROIChangeCB(self,value=None, char_value=None, **kw):
      posRBV = value
      ID = kw["ID"]
      self.emit(QtCore.SIGNAL("roiChangeSignal"),posRBV,ID)
      

    def processHighMagCursorChangeCB(self,value=None, char_value=None, **kw):
      posRBV = value
      ID = kw["ID"]
      self.emit(QtCore.SIGNAL("highMagCursorChangeSignal"),posRBV,ID)
      
    def processLowMagCursorChangeCB(self,value=None, char_value=None, **kw):
      posRBV = value
      ID = kw["ID"]
      self.emit(QtCore.SIGNAL("lowMagCursorChangeSignal"),posRBV,ID)
      

    def treeChangedCB(self,value=None, char_value=None, **kw):
      if (self.processID != self.treeChanged_pv.get()):
        self.emit(QtCore.SIGNAL("refreshTreeSignal"))

    def serverMessageCB(self,value=None, char_value=None, **kw):
      serverMessageVar = char_value
      self.emit(QtCore.SIGNAL("serverMessageSignal"),serverMessageVar)

    def serverPopupMessageCB(self,value=None, char_value=None, **kw):
      serverMessageVar = char_value
      self.emit(QtCore.SIGNAL("serverPopupMessageSignal"),serverMessageVar)

      
    def programStateCB(self, value=None, char_value=None, **kw):
      programStateVar = value
      self.emit(QtCore.SIGNAL("programStateSignal"),programStateVar)

    def pauseButtonStateCB(self, value=None, char_value=None, **kw):
      pauseButtonStateVar = value
      self.emit(QtCore.SIGNAL("pauseButtonStateSignal"),pauseButtonStateVar)

        
    def initUI(self):               
        self.tabs= QtGui.QTabWidget()
        self.text_output = Console(parent=self)
        self.comm_pv = PV(daq_utils.beamlineComm + "command_s")
        self.immediate_comm_pv = PV(daq_utils.beamlineComm + "immediate_command_s")
#        self.progressDialog = QtGui.QProgressDialog(QtCore.QString("Creating Requests"),QtCore.QString(),0,100)
        self.progressDialog = QtGui.QProgressDialog()
        self.progressDialog.setCancelButtonText(QtCore.QString())
        self.progressDialog.setModal(False)
        tab1= QtGui.QWidget()
        vBoxlayout1= QtGui.QVBoxLayout()
        splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical,self)
        splitter1.addWidget(self.tabs)
        self.setCentralWidget(splitter1)
        splitter1.addWidget(self.text_output)
        splitterSizes = [600,100]
#2/7/18        splitterSizes = [600,100]        
##commented 2/7/18        splitter1.setSizes(splitterSizes)
        importAction = QtGui.QAction('Import Spreadsheet...', self)
        importAction.triggered.connect(self.popImportDialogCB)

        modeGroup = QActionGroup(self);
        modeGroup.setExclusive(True)        
        self.userAction = QtGui.QAction('User Mode', self,checkable=True)
        self.userAction.triggered.connect(self.setUserModeCB)
        self.userAction.setChecked(True)
        self.expertAction = QtGui.QAction('Expert Mode', self,checkable=True)
        self.expertAction.triggered.connect(self.setExpertModeCB)        
        modeGroup.addAction(self.userAction)
        modeGroup.addAction(self.expertAction)

        
        
        exitAction = QtGui.QAction(QtGui.QIcon('exit24.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
#        exitAction.triggered.connect(self.close)
        exitAction.triggered.connect(self.closeAll)
        self.statusBar()
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(importAction)
        fileMenu.addAction(self.userAction)
        fileMenu.addAction(self.expertAction)        
        fileMenu.addAction(exitAction)

        self.setGeometry(300, 300, 1550, 1000) #width and height here. 
        self.setWindowTitle('LSDC')    
        self.show()

    def closeAll(self):
      QtGui.QApplication.closeAllWindows()

    def initCallbacks(self):
      self.treeChanged_pv = PV(daq_utils.beamlineComm + "live_q_change_flag")
      self.connect(self, QtCore.SIGNAL("refreshTreeSignal"),self.dewarTree.refreshTree)
      self.treeChanged_pv.add_callback(self.treeChangedCB)  
      self.mountedPin_pv = PV(daq_utils.beamlineComm + "mounted_pin")
      self.connect(self, QtCore.SIGNAL("mountedPinSignal"),self.processMountedPin)
      self.mountedPin_pv.add_callback(self.mountedPinChangedCB)  

      self.controlMaster_pv = PV(daq_utils.beamlineComm + "zinger_flag")
      self.connect(self, QtCore.SIGNAL("controlMasterSignal"),self.processControlMaster)
      self.controlMaster_pv.add_callback(self.controlMasterChangedCB)  

      self.choochResultFlag_pv = PV(daq_utils.beamlineComm + "choochResultFlag")
      self.connect(self, QtCore.SIGNAL("choochResultSignal"),self.processChoochResult)
      self.choochResultFlag_pv.add_callback(self.processChoochResultsCB)  
      self.xrecRasterFlag_pv = PV(daq_utils.beamlineComm + "xrecRasterFlag")
      self.xrecRasterFlag_pv.put("0")
      self.connect(self, QtCore.SIGNAL("xrecRasterSignal"),self.displayXrecRaster)
      self.xrecRasterFlag_pv.add_callback(self.processXrecRasterCB)  
      self.message_string_pv = PV(daq_utils.beamlineComm + "message_string") 
      self.connect(self, QtCore.SIGNAL("serverMessageSignal"),self.printServerMessage)
      self.message_string_pv.add_callback(self.serverMessageCB)  
      self.popup_message_string_pv = PV(daq_utils.beamlineComm + "gui_popup_message_string") 
      self.connect(self, QtCore.SIGNAL("serverPopupMessageSignal"),self.popupServerMessage)
      self.popup_message_string_pv.add_callback(self.serverPopupMessageCB)  
      self.program_state_pv = PV(daq_utils.beamlineComm + "program_state") 
      self.connect(self, QtCore.SIGNAL("programStateSignal"),self.colorProgramState)
      self.program_state_pv.add_callback(self.programStateCB)  
      self.pause_button_state_pv = PV(daq_utils.beamlineComm + "pause_button_state") 
      self.connect(self, QtCore.SIGNAL("pauseButtonStateSignal"),self.changePauseButtonState)
      self.pause_button_state_pv.add_callback(self.pauseButtonStateCB)  
#      self.sampx_pv = PV(daq_utils.motor_dict["sampleX"]+".VAL")
      self.sampx_pv = PV(daq_utils.motor_dict["sampleX"]+".RBV")      
      self.connect(self, QtCore.SIGNAL("sampMoveSignal"),self.processSampMove)
      self.sampx_pv.add_callback(self.processSampMoveCB,motID="x")
      self.sampy_pv = PV(daq_utils.motor_dict["sampleY"]+".RBV")
#      self.sampy_pv = PV(daq_utils.motor_dict["sampleY"]+".VAL")
##      self.connect(self, QtCore.SIGNAL("sampMoveSignal"),self.processSampMove)
      self.sampy_pv.add_callback(self.processSampMoveCB,motID="y")
      self.sampz_pv = PV(daq_utils.motor_dict["sampleZ"]+".RBV")
#      self.sampz_pv = PV(daq_utils.motor_dict["sampleZ"]+".VAL")
##      self.connect(self, QtCore.SIGNAL("sampMoveSignal"),self.processSampMove)
      self.sampz_pv.add_callback(self.processSampMoveCB,motID="z")

      self.omega_pv = PV(daq_utils.motor_dict["omega"] + ".VAL")
      self.omegaTweak_pv = PV(daq_utils.motor_dict["omega"] + ".RLV")      
      self.omegaRBV_pv = PV(daq_utils.motor_dict["omega"] + ".RBV")
#      self.omegaRBV_pv = PV(daq_utils.motor_dict["omega"] + ".VAL")      
#      self.connect(self, QtCore.SIGNAL("sampMoveSignal"),self.processSampMove)
      self.omegaRBV_pv.add_callback(self.processSampMoveCB,motID="omega") #I think monitoring this allows for the textfield to monitor val and this to deal with the graphics. Else next line has two callbacks on same thing.
#      self.sampleOmegaRBVLedit.getBasePV().add_callback(self.processSampMoveCB,motID="omega")      
      self.fastShutterRBV_pv = PV(daq_utils.motor_dict["fastShutter"] + ".RBV")
      self.connect(self, QtCore.SIGNAL("fastShutterSignal"),self.processFastShutter)      
      self.fastShutterRBV_pv.add_callback(self.shutterChangedCB)
#      self.omega_pv.add_callback(self.processSampMoveCB,motID="omega")

      if (1):

        self.connect(self, QtCore.SIGNAL("highMagCursorChangeSignal"),self.processHighMagCursorChange)
        self.highMagCursorX_pv.add_callback(self.processHighMagCursorChangeCB,ID="x")
        self.highMagCursorY_pv.add_callback(self.processHighMagCursorChangeCB,ID="y")      


        self.connect(self, QtCore.SIGNAL("lowMagCursorChangeSignal"),self.processLowMagCursorChange)
        self.lowMagCursorX_pv.add_callback(self.processLowMagCursorChangeCB,ID="x")
        self.lowMagCursorY_pv.add_callback(self.processLowMagCursorChangeCB,ID="y")      
        

        

    def popupServerMessage(self,message_s):

      if (self.popUpMessageInit):
        self.popUpMessageInit = 0
        return        
#      message = QtGui.QErrorMessage(self)
#      message.setModal(False)
      self.popupMessage.done(1)
      if (message_s == "killMessage"):
        return
      else:
        self.popupMessage.showMessage(message_s)


    def printServerMessage(self,message_s):
      if (self.textWindowMessageInit):
        self.textWindowMessageInit = 0
        return        
      print message_s
      self.text_output.showMessage(message_s)
      self.text_output.scrollContentsBy(0,1000)

    def colorProgramState(self,programState_s):
#      programState_s = beamline_support.pvGet(self.program_state_pv)
      if (string.find(programState_s,"Ready") == -1):
        self.statusLabel.setColor("yellow")
      else:
#        self.statusLabel.setColor("green")
        self.statusLabel.setColor("#99FF66")        
#        self.statusLabel.setColor("None")
        self.text_output.newPrompt()

    def changePauseButtonState(self,buttonState_s):
#      programState_s = beamline_support.pvGet(self.program_state_pv)
      self.pauseQueueButton.setText(buttonState_s)
      if (string.find(buttonState_s,"Pause") != -1):
#        self.pauseQueueButton.setStyleSheet("background-color: white")
        self.pauseQueueButton.setStyleSheet("background-color: None")                  
      else:
        self.pauseQueueButton.setStyleSheet("background-color: yellow")                    
#        self.pauseQueueButton.setColor("#99FF66")

    def controlEnabled(self):
      return (self.processID == abs(int(self.controlMaster_pv.get())) and self.controlMasterCheckBox.isChecked())
        
    def send_to_server(self,s):
      if (s == "lockControl"):
        self.controlMaster_pv.put(0-self.processID)
        self.text_output.newPrompt()        
#        self.controlMasterCheckBox.setChecked(True)        
        return
      if (s == "unlockControl"):
        self.controlMaster_pv.put(self.processID)
        self.text_output.newPrompt()        
        return
      if (self.controlEnabled()):
        if (0):
#        if (self.proposalID == -999999): #I'm not sure this is ever true            
          proposalID=daq_utils.getProposalID()
          text, ok = QtGui.QInputDialog.getInteger(self, 'Input Dialog','Enter your 6-digit Proposal ID:',value=proposalID)
          if ok:
#            print(str(text))
            daq_utils.setProposalID(int(text))
            self.proposalID = text

        time.sleep(.01)
        self.comm_pv.put(s)
      else:
        self.popupServerMessage("You don't have control")
      


    def aux_send_to_server(self,s):
      if (self.controlEnabled()):
        time.sleep(.01)
        self.immediate_comm_pv.put(s)
      else:
        self.popupServerMessage("You don't have control")


def main():
    daq_utils.init_environment()
    daq_utils.readPVDesc()    
    app = QtGui.QApplication(sys.argv)
    ex = controlMain()
    sys.exit(app.exec_())

#skinner - I think Matt did a lot of what's below and I have no idea what it is. 
if __name__ == '__main__':
    if '-pc' in sys.argv or '-p' in sys.argv:
        print 'cProfile not working yet :('
        #print 'starting cProfile profiler...'
        #import cProfile, pstats, io
        #pr = cProfile.Profile()
        #pr.enable()

    elif '-py' in sys.argv:
        print 'starting yappi profiler...'
        import yappi
        yappi.start(True)

    try:
        main()    

    finally:
        if '-pc' in sys.argv or '-p' in sys.argv:
            pass
            #pr.disable()
            #s = io.StringIO()
            #sortby = 'cumulative'
            #ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            #ps.print_stats()  # dies here, expected unicode, got string, need unicode io stream?
            #print(s.getvalue())

        elif '-py' in sys.argv:
            # stop profiler and print results
            yappi.stop()
            yappi.get_func_stats().print_all()
            yappi.get_thread_stats().print_all()
            print 'memory usage: {0}'.format(yappi.get_mem_usage())
