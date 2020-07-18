# glob-from-gitignore

#### Description
Using the [gitignore-to-glob](https://www.npmjs.com/package/gitignore-to-glob) node package to translate the various declarations within a specified `.gitignore` file to output the list of ignore specifications as standard file `globs`.

##### Required Arguments
* Gitignore: The only required argument is one or more `.gitignore` input files to be converted to file spcification `globs`.
  For example:
  ``` bash
  # Parse the global ignore paths specified in the $HOME directory
  glob-from-gitignore.js $HOME/.gitignore_global
  **/*.py[cod]|**/*.py[cod]/**
  # Parse the global ignore paths specified in the $HOME directory and the ignore paths within the current directory
  glob-from-gitignore.js $HOME/.gitignore_global .gitignore
  **/*.py[cod]|**/*.py[cod]/**
  ```

##### Options
* Verbose: To enable richer debug output pass the `--verbose` or `-v` option.
  ``` bash
  # Specify verbose output
  glob-from-gitignore.js --verbose $HOME/.gitignore_global
  ignore: **/*.py[cod]
  ignore: **/*.py[cod]/**
  **/*.py[cod]|**/*.py[cod]/**
  ```

* Negate: The [gitignore-to-glob](https://www.npmjs.com/package/gitignore-to-glob) package returns the set of globs all `negated`.
  For example:
  ``` bash
  # if the .gitignore file specified ignoring python bytecode: *.pyc
  # the package would return:
  !*.pyc
  ```
  I believe this was done so it was possible to `glob` for all files ***except*** those within the `gitignore` specification.  Which makes sense for a certain use case.  Unfortunately, my use case was the opposite.  I needed all the `glob` patterns within the `gitignore` file which specified the actual ignored files (without the negation enabled).  Therefore, the ***default behaviour*** is to return a list of non-negated `gitignore` `glob` specifications.<br>
  To enable the negation simply pass the `--negate` or the `-n` option.
  For example:
  ``` bash
  # Negate the globs being returned
  glob-from-gitignore.js --negate $HOME/.gitignore_global
  !**/*.py[cod]|!**/*.py[cod]/**
  # DO NOT negate the globs
  glob-from-gitignore.js $HOME/.gitignore_global
  **/*.py[cod]|**/*.py[cod]/**
  ```

* Seperator: When outputting the list of `gitignore` converted `glob`'s it's possible to specify the seperator.  The default is the simple `|` (`pipe symbol`) as a seperator between the multiple `gitignore` converted `glob`'s.  Using the `--seperator "<text>"` it should be possible to specify anything from a newline to a `, ` (`comma+space`).
  For example:
  ``` bash
  # output using a space between globs
  glob-from-gitignore.js --seperator ' ' $HOME/.gitignore_global
  **/*.py[cod] **/*.py[cod]/**

  # output using a comma+space between globs
  glob-from-gitignore.js --seperator ', ' $HOME/.gitignore_global
  **/*.py[cod], **/*.py[cod]/**

  # EXPERT: output using a newline between globs
  glob-from-gitignore.js --seperator "$(printf \"\\n\")" $HOME/.gitignore_global
  **/*.py[cod]
  **/*.py[cod]/**

  # EXPERT: output using a horizontal tab between globs
  glob-from-gitignore.js --seperator "$(printf \"\\t\")" $HOME/.gitignore_global
  **/*.py[cod]    **/*.py[cod]/**
  ```

* Wrapper: When outputting the list of `gitignore` converted `glob`'s it's also possible to wrap each `glob` in some type of wrapper.  For exaqmple, its possible to specify the `"` as the wrapper and each individual `glob` will be wrapped in quotes.  If this is used in conjunction with the `--seperator ', '` option it will output an initializer for an array (minus the begin `[` and end `]` braces. 
  For example:
  ``` bash
  # output using a " quote wrapper and a comma+space seperator
  glob-from-gitignore.js --wrapper '"' --seperator ', ' $HOME/.gitignore_global
  "**/*.py[cod]", "**/*.py[cod]/**"
  ```

<br>

At this point we are beginning to get into the realm of what `awk` and `sed` do much better.  If further parsing, quoting, splicing and dicing is required I would recommend those utilities as they are better suited for those tasks.
