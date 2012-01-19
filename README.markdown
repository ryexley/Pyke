## Pyke ##
Pyke is a Python based build module for .NET projects on Windows [0]. Ultimately its really just a class with a collection of operations commonly used for building and packaging .NET projects; you know, things like generating and applying version numbers, performing compilation, generating Nuget spec files and packages, and more planned (if I ever have need and get around to it).

## Dependencies ##
* _[Python](http://python.org/download/)_: obviously...
* _[MSBuild](http://msdn.microsoft.com/en-us/library/wea2sca5(v=vs.90).aspx)_: used for compilation
* _[Nuget](http://nuget.codeplex.com/)_: used for package generation, this module depends on the nuget.exe command line bootstrapper, which can be downloaded [here](http://nuget.codeplex.com/releases/view/58939).

## Documentation and usage examples ##
For now, all of the documentation for the module can be found in the pyke.py file itself, but that's starting to get pretty heavy and unnecessary, so I'm gradually working my way towards pulling that out of the file and into here. Until I get to that, check in the file itself.

## Why? ##
Aren't there plenty of other build tools out there for .NET? Sure there are. But frankly, none of them were really what I wanted out of a build tool. I've grown so tired over the years of wrestling with XML, so NAnt and raw MSBuild files are just totally unappealing to me anymore. What about Rake? Albacore? Yeah, I gave that a shot too, but I was never able to get it to work consistently using the examples I found around the interwebs. Not really sure why, but it just never worked out for me. Powershell? Psake? That was actually what I originally started with when trying to write this module, but I've yet to be able to wrap my head around how Powershell works for most things, and good documentation and examples for how to do some fairly basic things (like file I/O operations, which this module uses heavily) are difficult to find at best...it just took me too long to figure out how to get things done with Powershell.

Ultimately, Python gave me the _it just works_ factor. The documentation is fantastic, and the syntax is easy to understand and read, and it was fairly easy to hit the ground running and get this thing knocked out. When all was said and done, I had the bulk/core of this module written and working within about eight hours of coding...having _never_ written a single line of Python before. And when I ran it...it worked.

So...thats why.

_**DISCLAIMER**: This is *literally* the first Python code I've ever written. I'm nearly 100% certain there's a lot in here that could be done better. Constructive feedback is welcome._

[0]: NOTE that this module is intended for use ONLY on Windows operating systems. If desired, it could be fairly easily retrofitted to use the Mono compiler for use on *nix if desired, but that is beyond the original scope of intent for the module.
