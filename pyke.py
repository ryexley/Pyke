"""
Pyke, a Python make tool for .NET

This class contains common functions useful for building and packaging .NET based
applications.

Dependencies:
	MSBuild: 
		Pyke uses MSBuild to compile .NET projects. It will need to be available
		and you will need to know and provide the path to it.
	Nuget: 
		If you wish to use Pyke to generate Nuget packages, you will need to have
		the Nuget command line tool available on your computer and will need to
		know and provide the full path to it. If you don't have it installed, it
		can be downloaded from the following URL:
			http://nuget.codeplex.com/releases/view/58939

Usage:
	The following sample snippet uses Pyke to build and package a web application project, and 
	can be copied and pasted into a build script to get you started:

	>% ==== START SNIP HERE ==== %<

	import pyke, os, shutil

	p = pyke.pyke(basedir = os.curdir)
	projectFile = "Your.Web.csproj"
	version = p.getVersion()
	assemblyInfo = {
		"ClsCompliant" : "false",
		"ComVisible" : "false",
		"Title" : "Your Web Application",
		"Description" : "A description of Your Web Application",
		"Company" : "Your company/organization name",
		"Product" : "Your Product Name",
		"Copyright" : "Copyright 2011-2012, Your Company Name, All rights reserved",
		"Version" : "1.0",
		"InformationalVersion" : version,
		"FileVersion" : version
	}

	# Build the web project in release configuration
	p.build(projectFile = projectFile, configuration = "release", assemblyInfo = assemblyInfo)

	# Create a clean directory, with everything where it needs to be, in preparation for packaging
	packageSourceDir = os.path.join(p.basedir, "PackageSource")
	if not os.path.exists(packageSourceDir) :
		os.makedirs(packageSourceDir)
	else :
		p.cleanDir(packageSourceDir)

	p.copyFolderContents(os.path.join(p.buildOutputDir, "_PublishedWebsites", "Your.Web"), os.path.join(p.basedir, "PackageSource"))

	# Build Nuget package
	deploymentPackagesFolder = os.path.join(p.basedir, "DeploymentPackages")
	if not os.path.exists(deploymentPackagesFolder) :
		os.makedirs(deploymentPackagesFolder)
	nb.packageNuget(targetDir = packageSourceDir, specName = os.path.splitext(projectFile)[0], version = version, outputDir = deploymentPackagesFolder)

	# Cleanup
	p.cleanDir(nb.buildOutputDir)
	p.cleanDir(packageSourceDir)
	os.rmdir(p.buildOutputDir)
	os.rmdir(packageSourceDir)

	>% ==== END SNIP HERE ==== %<

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

	compileProject:
		Calls MSBuild to compile the given projectFile with the given build configuration

	formatAssemblyInfoFileContent:
		Returns the formatted content for generated AssemblyInfo.cs files with the given assemblyInfo attributes

	generateAssemblyInfoFiles:
		Renames the original AssemblyInfo.cs files returned by getAssemblyInfoFiles and 
		Creates new AssemblyInfo.cs files with the content returned from formatAssemblyInfoFileContent

	restoreOriginalAssemblyInfoFiles:
		Deletes the AssemblyInfo.cs files created by generateAssemblyInfoFiles, and restores the original
		AssemblyInfo.cs files
	
	cleanDir:
		Utility function for cleaning out (emptying, deleting all files) the given target directory
	
	copyFolderContents:
		Utility function for copying the contents of the given sourceDir into the given targetDir (and
		creates the given targetDir if it doesn't already exist)

	formatBlock:
		Utility operation that takes a multi-line block of text (without normally required string
		endings and concatenation) and returns an appropriately formatted block of concatenated text.
		(Found here: http://code.activestate.com/recipes/145672-multi-line-string-block-formatting/)

	writeBannerMessage:
		Utility operation for printing a formatted banner message to standard output
	
	packageNuget:
		Generates a Nuget package spec file, and uses it to generate a Nuget package with the
		given specName, version, targetDir and outputDir.
	
	generateNuspec:
		Generates a Nuget package spec file with the given specName against the given targetDir
	
	generateNuspec:
		Creates a custom Nuget package spec file merging the give specFileTemplate and the given
		content in the given targetDir.
	
	generateNugetPackage:
		Generates a Nuget package with the given version and specFile to the given outputDir against
		the given targetDir.

TODO:
	* Need to figure out a good way to handle cleanup on failed execution (exceptions, etc)
	* Add docstrings to class operations
	* Add logging - replace print statements with logging (http://docs.python.org/library/logging.html)
	* Check for the existence of the WINDIR environment variable. Raise exception if it can't be resolved
	* Use os.walk to find MSBuild and Nuget (just to add some robustness)
	* Add the ability to specify a framework version for build (should be used to determine the MSBuild location)
	* Unit test execution

"""

__author__ = "Bob Yexley (bob@yexley.net)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2012/01/15 $"
__copyright__ = "Copyright (c) 2012 You"
__license__ = "Public domain (use at your own risk)"

import os, shutil, fnmatch, shlex, subprocess, re, getpass
import datetime as dt

class pyke :

	def __init__ (
		self, 
		basedir = None, 
		msbuild = None, 
		outputDir = None, 
		nuget = None) :
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
		
		if nuget == None :
			self.nuget = os.path.join("C:\\", "nuget", "nuget.exe")
		else :
			self.nuget = nuget
		
		self.assemblyInfoFiles = self.getAssemblyInfoFiles()
		self.user = getpass.getuser()
	
	def build(
		self, 
		projectFile = None, 
		configuration = "debug", 
		assemblyInfo = None, 
		version = None) :
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
		self.compileProject(projectFile = projectFile, configuration = configuration)
		self.restoreOriginalAssemblyInfoFiles()
	
	def cleanDir(self, target) :
		for root, dirs, files in os.walk(target, topdown = False) :
			for name in files :
				os.remove(os.path.join(root, name))
			for name in dirs :
				os.rmdir(os.path.join(root, name))
	
	def compileProject(
		self, 
		configuration, 
		projectFile = None) :
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
			self.cleanDir(self.buildOutputDir)
		
		self.writeBannerMessage("Compiling to output directory: %s" % self.buildOutputDir)

		compileOutput = subprocess.call([self.msbuild, buildConfiguration, buildTargets, output])

		if compileOutput == 1 : # build error
			# cleanup assembly info files if the build failed
			self.restoreOriginalAssemblyInfoFiles()

		print compileOutput
	
	def copyFolderContents(
		self, 
		sourceDir, 
		targetDir) :
		try :
			if os.path.exists(targetDir) :
				self.cleanDir(targetDir)
				os.rmdir(targetDir)
			else :
				os.makedirs(targetDir)

			shutil.copytree(sourceDir, targetDir)
		except OSError :
			raise Exception("Unable to copy directory contents: \n%s" % osex)

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

	def generateNugetPackage(
		self, 
		version = None, 
		specFile = None, 
		targetDir = None, 
		outputDir = None) :
		if not os.path.isfile(self.nuget) :
			raise Exception("Unable to resolve path to Nuget command line tool (%s)" % self.nuget)
		
		if specFile == None and targetDir == None :
			raise Exception("Can't generate a nuget package without specifying either a nuspec file or a directory that contains a nuspec file.")
		
		args = []
		args.append('"%s"' % self.nuget)
		args.append("pack")

		if specFile != None :
			args.append('"%s"' % specFile)

		if version != None :
			args.append("-Version %s" % version)
		
		if outputDir != None :
			args.append('-OutputDirectory "%s"' % outputDir)
		
		args.append("-NoPackageAnalysis")

		if targetDir != None :
			workingDir = targetDir
		else :
			workingDir = self.basedir

		command = " ".join(args)
		processInput = shlex.split(command)

		packOutput = subprocess.Popen(processInput, executable = self.nuget, cwd = workingDir, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
		print packOutput.stdout.read()

	def generateNuspec(
		self, 
		targetDir, 
		specName = None) :
		if not os.path.isfile(self.nuget) :
			raise Exception("Unable to resolve path to Nuget command line tool (%s)" % self.nuget)

		if specName == None :
			if self.projectFile != None :
				self.specName = os.path.splitext(self.projectFile)[0]
		else :
			self.specName = specName
		
		command = "nuget spec -Force %s" % self.specName

		args = shlex.split(command)
		
		specOutput = subprocess.Popen(args, executable = self.nuget, cwd = targetDir, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
		print specOutput.stdout.read()
	
	def generateNuspec(
		self, 
		targetDir, 
		specFileTemplate, 
		specFileName = None, 
		content = None) :
		if not os.path.exists(targetDir) :
			raise Exception("Unable to resolve targetDir path")
		
		if content != None :
			fileContent = specFileTemplate % content
		else :
			fileContent = specFileTemplate
		
		try :
			specFile = open(os.path.join(targetDir, self.resolveSpecFileName(specFileName)), "w")
			try :
				specFile.writelines(fileContent)
			finally :
				specFile.close()
		except IOError :
			raise Exception("Error generating Nuget spec file")

	def getAssemblyInfoFiles(self) :
		asmInfoFiles = []
		for path, dirs, files in os.walk(os.path.abspath(self.basedir)) :
			for filename in fnmatch.filter(files, "AssemblyInfo.cs") :
				asmInfoFiles.append(os.path.join(path, filename))
		return asmInfoFiles
	
	def getProjectFilePath(self, filename) :
		for path, dirs, files in os.walk(os.path.abspath(self.basedir)) :
			for filename in fnmatch.filter(files, filename) :
				return os.path.abspath(os.path.join(path, filename))

	def getVersion(self) :
		now = dt.datetime.now()
		version = now.strftime("%Y.%m.%d.%H%M")
		return version
	
	def packageNuget(
		self, 
		targetDir, 
		specName = None, 
		version = None, 
		outputDir = None) :
		if not os.path.isfile(self.nuget) :
			raise Exception("Unable to resolve path to Nuget command line tool (%s)" % self.nuget)

		if not os.path.exists(targetDir) :
			raise Exception("A directory containing the desired package contents must be specified for package generation")
		
		if specName == None :
			raise Exception("A name for the package spec file must be provided")
		else :
			self.packageSpecFile = specName

		self.generateNuspec(targetDir = targetDir, specName = self.packageSpecFile)
		self.generateNugetPackage(
			version = version, 
			specFile = os.path.join(targetDir, "%s.nuspec" % specName), 
			outputDir = outputDir)
	
	def packageNuget(
		self, 
		targetDir, 
		specFileTemplate, 
		specFileName = None, 
		content = None, 
		version = None, 
		outputDir = None) :
		if not os.path.isfile(self.nuget) :
			raise Exception("Unable to resolve path to Nuget command line tool (%s)" % self.nuget)

		if not os.path.exists(targetDir) :
			raise Exception("A directory containing the desired package contents must be specified for package generation")
		
		self.generateNuspec(
			targetDir = targetDir, 
			specFileTemplate = specFileTemplate, 
			specFileName = specFileName, 
			content = content)
		self.generateNugetPackage(
			version = version, 
			specFile = os.path.join(targetDir, self.resolveSpecFileName(specFileName)), 
			outputDir = outputDir)
	
	def resolveSpecFileName(self, specFileName = None) :
		if specFileName != None :
			specFileNameParts = os.path.splitext(specFileName)
			specFileNameLast = len(specFileNameParts)
	
			if specFileNameParts[specFileNameLast -1] != ".nuspec" :
				fileName = "%s.nuspec" % specFileName
			else :
				fileName = specFileName
		else :
			if self.projectFile != None :
				fileName = "%s.nuspec" % os.path.splitext(self.projectFile)[0]
			else :
				fileName = "package.nuspec"
		
		return fileName
	
	def restoreOriginalAssemblyInfoFiles(self) :
		for asmInfoFile in self.assemblyInfoFiles :
			try :
				os.remove(asmInfoFile)
				os.rename("%s.build-temp" % asmInfoFile, asmInfoFile)
			except IOError :
				raise Exception("Error restoring original AssemblyInfo file: %s" % asmInfoFile)

	def writeBannerMessage(self, message) :
		bannerMessage = self.formatBlock(
			"""

			======================================================================
			%s
			======================================================================

			"""
		)

		print bannerMessage % message
