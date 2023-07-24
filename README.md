# pydise
***This script is designed to detect Python scripts that generate side effects when imported into another code.***

Side effects refer to unintended changes to the global state of the system, such as writing files, or displaying undesired outputs when a script is imported without being directly executed.

**Example of side effects** : 
```python
# my_lib.py
print("42")
class MyLib(object):
    pass

# my_script.py
>>> import my_lib
42
```

That's what we want to avoid.

# How it works

The script analyzes the content of Python files specified in the source directory to identify elements which may indicate side effects, eg :

    * print("hello")
    * open("myfile", "rw")
    * exit()
    * if True:
         exit()
    ...

We used AST, so no code are executed.

The script then provides a report of the files that potentially contain side effects so that you can identify and correct them if necessary.

# Usage

```
$ pip install pydise
$ pydise
```

Example :

``` python
# my_lib.py
print("42")
class MyLib(object):
    pass
```

``` python
$ pydise
ERROR:root:.\my_lib.py:1 -> Side effects detected : print
```

# Arguments

## Positional arguments:
  **filename** : `file to check (wildcard)`

*Example* : 

```
$ pydise mylib.py
$ pydise *.py
$ pydise .
```

## Options:


  **--list-only** : `list the detected files without checking errors.`

*Example* : 

```
$ pydise --list-only
Detected files : 
* .\my_lib.py
* .\my_lib2.py
```

  **--pattern-ignored** : `ignore line containing the pattern, multiple patterns can be setted, the pattern is added to the default patterns.`

*default patterns* : `# no-pydise` or `# no_pydise`

``` python
# my_lib.py
print("42")  # ignoredthisline
class MyLib(object):
    pass
```

``` python
$ pydise --pattern-ignored ignoredthisline --pattern-ignored anotherpattern
```

# Contributions

I am a self-taught developer, it's highly possible that my code could be buggy / optimizable, so any contributions to improving this script are welcome! 
If you find issues or want to add new features, feel free to create a pull request.

# Disclaimer

Make sure you understand the implications of using this script as it may generate false positives or fail to detect certain side effects, depending on the complexity of the analyzed code. It is recommended to manually review the report results before making critical decisions regarding your code.

# License

This project is licensed under the MIT License - you can use, modify, and distribute it freely while retaining the original license notice.
