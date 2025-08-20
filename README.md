# JopPyLib
Python abstraction over the Joplin data api  
  
==WARNING==  
JopPyLib is under heavy development. I've only just started. I will update this readme when a first usable version is released.

JopPyLib is part of the [Artumis project](https://jeroenkroesen.github.io/artumis_site/). It is meant to be a thin layer to enable programmatic manipulation of Joplin notes via a higher level interface than the data API.  
  
JopPyLib is highly opinionated because it is designed to enable a higher level library call [JopBrainLib](https://github.com/jeroenkroesen/jopbrainlib) that enables second brain functionality in Joplin.  
  
An [example Jupyter notebook interface](https://github.com/jeroenkroesen/joppylib-notebook) is available for interacting with JopPyLib.  
***  
  
## Status
Current release: joppylib-0.1.0a9-py3-none-any
Very alpha testing release.
***  
  
  
## Roadmap
- [x] Clean up and document old personal codebase
- [ ] Complete api layer (`api_client.py`)
    - [x] Generate packages on github to allow pip install when testing.
    - [x] Implement PUT
    - [x] Implement better tag functions
        - [x] Delete tag from note
        - [x] Get all tags attached to a note
    - [ ] Test API functionality
    - [x] Demonstrate low-level interface in [notebook](https://github.com/jeroenkroesen/joppylib-notebook)
- [x] Design higher level interface
- [x] Implement higher level interface  

***
  
  
## Reference
[Joplin Data API documentation](https://joplinapp.org/help/api/references/rest_api/)
