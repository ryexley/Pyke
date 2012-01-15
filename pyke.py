"""
Pyke, a Python make tool for .NET

This class contains common functions useful for building and packaging .NET based
applications.

Usage:
	The following can be copied and pasted into a build script to get you started:

	import pyke, os

	builder = pyke.pyke(basedir = os.curdir)
	projectFile = "YourProject.csproj"
	version = builder.getVersion()
	assemblyInfo = {
		"ClsCompliant" : "false",
		"ComVisible" : "false",
		"Title" : "Carbon",
		"Description" : "Food Donation Connection core web platform",
		"Company" : "Food Donation Connection",
		"Product" : "Carbon",
		"Copyright" : "Copyright 2011-2012, Fo Donation Connection, All rights reserved",
		"Version" : "1.0",
		"InformationalVersion" : version,
		"FileVersion" : version
	}

	builder.build(projectFile = projectFile, configuration = "release", assemblyInfo = assemblyInfo)

	From a command prompt, execute the script as follows (replace build.py with the name of your script
	if you named it differently):
		C:\Path\to\your\project\folder> python build.py

API:
	These are the functions that Pyke makes available for use in your build scripts:

	getAssemblyInfoFiles: 
		Returns a list of all of the AssemblyInfo.cs files found recursively below basedir

	getVersion:
		Returns a date-based version string in the form of year.month.day.HourMinute (i.e. 2012.01.14.2317)

	getProjectFilePath:
		Returns the absolute path to the location of the given filename argument below basedir

	build:
		Performs the following build actions:
			* calls generateAssemblyInfoFiles to apply the given assemblyInfo attributes to prep 
			  assemblies for compilation
			* calls compile with the absolute path to the given project file and build configuration
			* calls restoreOriginalAssemblyInfoFiles

	compile:
		Calls MSBuild to compile the given projectFile with the given build configuration

	formatAssemblyInfoFileContent:
		Returns the formatted content for generated AssemblyInfo.cs files with the given assemblyInfo attributes

	generateAssemblyInfoFiles:
		Renames the original AssemblyInfo.cs files returned by getAssemblyInfoFiles and 
		Creates new AssemblyInfo.cs files with the content returned from formatAssemblyInfoFileContent

	restoreOriginalAssemblyInfoFiles:
		Deletes the AssemblyInfo.cs files created by generateAssemblyInfoFiles, and restores the original
		AssemblyInfo.cs files

	formatBlock:
		Utility operation that takes a multi-line block of text (without normally required string
		endings and concatenation) and returns an appropriately formatted block of concatenated text.
		(Found here: http://code.activestate.com/recipes/145672-multi-line-string-block-formatting/)

	writeBannerMessage:
		Utility operation for printing a formatted banner message to standard output

TODO:
	* Nuget package generation
	* Unit test execution

"""

__author__ = "Bob Yexley (bob@yexley.net)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2012/01/15 $"
__copyright__ = "Copyright (c) 2012 You"
__license__ = "Public domain (use at your own risk)"

import os, fnmatch, subprocess, re, getpass
import datetime as dt

class pyke :

	msbuild = os.path.join(os.environ["WINDIR"], "Microsoft.NET", "Framework64", "v4.0.30319", "msbuild.exe")

	def __init__ (self, basedir = None, msbuild = None, outputDir = None) :
		if basedir == None :
			self.basedir = os.path.abspath(os.curdir)
		else :
			self.basedir = os.path.abspath(basedir)

		if msbuild == None :
			self.msbuild = os.path.join(os.environ["WINDIR"], "Microsoft.NET", "Framework64", "v4.0.30319", "msbuild.exe")
		else :
			self.msbuild = msbuild
		
		if outputDir == None :
			self.buildOutputDir = os.path.join(self.basedir, "BuildOutput")
		else :
			self.buildOutputDir = outputDir
		
		self.assemblyInfoFiles = self.getAssemblyInfoFiles()
		self.user = getpass.getuser()

	def getAssemblyInfoFiles(self) :
		asmInfoFiles = []
		for path, dirs, files in os.walk(os.path.abspath(self.basedir)) :
			for filename in fnmatch.filter(files, "AssemblyInfo.cs") :
				asmInfoFiles.append(os.path.join(path, filename))
		return asmInfoFiles

	def getVersion(self) :
		now = dt.datetime.now()
		version = now.strftime("%Y.%m.%d.%H%M")
		return version
	
	def getProjectFilePath(self, filename) :
		for path, dirs, files in os.walk(os.path.abspath(self.basedir)) :
			for filename in fnmatch.filter(files, filename) :
				return os.path.abspath(os.path.join(path, filename))
	
	def build(self, projectFile = None, configuration = "debug", assemblyInfo = None, version = None) :
		if projectFile == None :
			raise Exception("No project or solution file specified")
		
		if assemblyInfo == None :
			self.assemblyInfo = {
				"ClsCompliant" : "false",
				"ComVisible" : "false",
				"Title" : "",
				"Description" : "",
				"Company" : "",
				"Product" : "",
				"Copyright" : "",
				"Version" : "1.0",
				"InformationalVersion" : "1.0 (%s)" % configuration,
				"FileVersion" : "1.0"
			}
		else :
			self.assemblyInfo = assemblyInfo
		
		# Append additional details to assembly title/description
		# Remove this (or comment it out) if you don't wish to have the additional details included in the assembly/file title/description
		self.assemblyInfo["Title"] = "%s (compilation: %s, built by: %s)" % (self.assemblyInfo["Title"], configuration, self.user.lower())
		
		if version == None :
			self.version = self.getVersion()
		else :
			self.version = version
		
		self.generateAssemblyInfoFiles(assemblyInfo)
		self.compile(projectFile = projectFile, configuration = configuration)
		self.restoreOriginalAssemblyInfoFiles()
	
	def compile(self, configuration, projectFile = None) :
		if projectFile == None :
			raise Exception("No project or solution file specified")
		else : 
			if os.path.exists(os.path.join(self.basedir, projectFile)) :
				projectFilePath = os.path.join(self.basedir, projectFile)
			else :
				projectFilePath = self.getProjectFilePath(projectFile)
		
		if not os.path.exists(projectFilePath) :
			raise Exception("Unable to resolve path to the given project file")

		buildTargets = "/t:Clean;Rebuild"
		buildConfiguration = "/p:Configuration=%s" % configuration
		output = "/p:OutputPath=%s" % self.buildOutputDir

		if not os.path.exists(self.buildOutputDir) : # create the build output directory if it doesn't exist
			os.makedirs(self.buildOutputDir)
		else : # otherwise, if it exists, make sure there's nothing in it before we send build output into it
			for root, dirs, files in os.walk(self.buildOutputDir, topdown = False) :
				for name in files :
					os.remove(os.path.join(root, name))
				for name in dirs :
					os.rmdir(os.path.join(root, name))
		
		self.writeBannerMessage("Compiling to output directory: %s" % self.buildOutputDir)

		compileOutput = subprocess.call([self.msbuild, buildConfiguration, buildTargets, output])

		if compileOutput == 1 : # build error
			# cleanup assembly info files if the build failed
			self.restoreOriginalAssemblyInfoFiles()

		print compileOutput

	def formatAssemblyInfoFileContent(self, assemblyInfo) :
		fileContent = self.formatBlock(
			"""
			using System;
			using System.Reflection;
			using System.Runtime.CompilerServices;
			using System.Runtime.InteropServices;

			[assembly: CLSCompliantAttribute(%(ClsCompliant)s)]
			[assembly: ComVisibleAttribute(%(ComVisible)s)]
			[assembly: AssemblyTitleAttribute("%(Title)s")]
			[assembly: AssemblyDescriptionAttribute("%(Description)s")]
			[assembly: AssemblyCompanyAttribute("%(Company)s")]
			[assembly: AssemblyProductAttribute("%(Product)s")]
			[assembly: AssemblyCopyrightAttribute("%(Copyright)s")]
			[assembly: AssemblyVersionAttribute("%(Version)s")]
			[assembly: AssemblyInformationalVersionAttribute("%(InformationalVersion)s")]
			[assembly: AssemblyFileVersionAttribute("%(FileVersion)s")]
			[assembly: AssemblyDelaySignAttribute(false)]
			"""
		)

		return fileContent % self.assemblyInfo
	
	def generateAssemblyInfoFiles(self, assemblyInfo) :
		for asmInfoFile in self.assemblyInfoFiles :
			try :
				os.rename(asmInfoFile, "%s.build-temp" % asmInfoFile)
				newFile = open(asmInfoFile, "w")
				try :
					fileContent = self.formatAssemblyInfoFileContent(assemblyInfo)
					newFile.writelines(fileContent)
				finally :
					newFile.close()
			except IOError :
				raise Exception("Error generating AssemblyInfo file")
	
	def restoreOriginalAssemblyInfoFiles(self) :
		for asmInfoFile in self.assemblyInfoFiles :
			try :
				os.remove(asmInfoFile)
				os.rename("%s.build-temp" % asmInfoFile, asmInfoFile)
			except IOError :
				raise Exception("Error restoring original AssemblyInfo file: %s" % asmInfoFile)

	def formatBlock(self, block) :
		lines = str(block).split("\n")
		while lines and not lines[0] : del lines[0]
		while lines and not lines[-1] : del lines[-1]
		ws = re.match(r"\s*", lines[0]).group(0)
		if ws :
			lines = map(lambda x : x.replace(ws, "", 1), lines)
		while lines and not lines[0] : del lines[0]
		while lines and not lines[-1] : del lines[-1]

		return "\n".join(lines) + "\n"

	def writeBannerMessage(self, message) :
		bannerMessage = self.formatBlock(
			"""

			======================================================================
			%s
			======================================================================

			"""
		)

		print bannerMessage % message
