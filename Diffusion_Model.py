import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *

#set environment variables

sPath = r"H:\Modeling with Raster\Lab11\Lab11_data\Lab11_Data\HydroModeling\Lab11.gdb"
arcpy.env.workspace = sPath

arcpy.env.cellSize = "bethel"
arcpy.env.extent = "bethel"
arcpy.env.outputCoordinateSystem = "bethel"
arcpy.env.mask = "bethel"
arcpy.env.overwriteOutput = True

arcpy.CheckOutExtension("Spatial")

def getRasters(tag):
	selected_rasters = []
	rasters = arcpy.ListRasters("*","GRID")
	for raster in rasters:
		if tag in raster:
			selected_rasters.append(raster)
	return selected_rasters

def getAttributes(inLayer,fieldName):
	attributes = []
	data = arcpy.SearchCursor(inLayer)
	for row in data:
		attributes.append(row.getValue(fieldName))
	attributes.sort()	
	return attributes

def getCellSize(inRaster):
	cellSize_resultObject = arcpy.GetRasterProperties_management(inRaster,"CELLSIZEX","")
	return int(cellSize_resultObject.getOutput(0))

def getRasterStats(inRaster, stat):
	rasterStat = arcpy.GetRasterProperties_management(inRaster, stat,"")
	return float(rasterStat.getOutput(0))

def analyzeSinks(raster):
	print("filling raster...")
	filledRaster = Fill(raster)
	filledRaster.save(raster+"_filled")

	print("finding raster difference...")
	diffRaster = raster - filledRaster
	#diffRaster = Minus(raster,filledRaster)
	diffRaster.save(raster+"_diff")
	diffValues = getAttributes(diffRaster,"value")
	print("max sink depth: " +str(diffValues[0]))

	print("calculating number of sinks...")
	groupedSinks = RegionGroup(diffRaster, "EIGHT", "CROSS","",0)
	groupedSinks.save(raster+"_grouped")
	groupedValues = getAttributes(groupedSinks,"value")
	print("Number of Sinks: "+str(len(groupedValues)))

def computeFlow(inRaster):
	print("computing flow direction...")
	flowDirection = FlowDirection(inRaster,"","")
	flowDirection.save(inRaster+"_dir")

	print("computing flow accumulation...")
	flowAccumulation = FlowAccumulation(flowDirection, "","")
	flowAccumulation.save(inRaster+"_accum")

	print("computing flow length...")
	flowLength = FlowLength(flowDirection, "DOWNSTREAM","")
	flowLength.save(inRaster+"_length")

	print("extracting stream channel...")
	streamChannel = Con(inRaster+"_accum",1,0,"value > 200")
	streamChannel.save(inRaster+"_channel")

def delineateWatershed(streamRaster, flowDirRaster, pourPointData):
	print("computing stream order...")
	streamOrder = StreamOrder(streamRaster, flowDirRaster, "STRAHLER")
	streamOrder.save(streamRaster+"_order")
	streamOrders = getAttributes(streamOrder, "value")
	print("Highest Stream Order: "+str(streamOrders[-1]))

	print("delineating watershed...")
	watershed = Watershed(flowDirRaster, pourPointData, "ID")
	watershed.save(streamRaster+"_watershed")
	#calculate watershed area
	watershedData = getAttributes(watershed, "count")
	totalArea = sum(watershedData)*(getCellSize(watershed)**2)
	print("Watershed Area: "+str(totalArea))
	#calculate flow accumulation at the whiteoak guage
	ExtractValuesToPoints(pourPointData, "bethel_filled_accum", pourPointData+"_accum","","")
	flowAccumAtGuage = getAttributes(pourPointData+"_accum", "RASTERVALU")
	print("Flow at Guage: "+str(flowAccumAtGuage))
	#calculate upstream flow length
	ExtractValuesToPoints(pourPointData, "bethel_filled_length", pourPointData+"_length","","")
	# flowLengths = getAttributes("bethel_filled_length", "Value")
	flowLengthAtGauge = getAttributes(pourPointData+"_length","RASTERVALU")
	maxFlow = getRasterStats("bethel_filled_length","MAXIMUM")
	minFlow = getRasterStats("bethel_filled_length","MINIMUM")
	upstreamLength = flowLengthAtGauge[0]-maxFlow
	print("Upstream Length: "+str(upstreamLength))
	downstreamLength = flowLengthAtGauge[0]-minFlow
	print("Downstream Length: "+str(downstreamLength))


delineateWatershed("bethel_filled_channel", "bethel_filled_dir", "whiteoak_gauge")

#analyzeSinks("bethel")
#computeFlow("bethel_filled")


