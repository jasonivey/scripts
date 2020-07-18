#!/usr/bin/env node
const gitignore_to_glob = require('gitignore-to-glob');
const expandenv = require('expandenv');
const yargs = require("yargs");

const argv = yargs
    .scriptName('glob-from-gitignore.js')
    .usage('Usage: $0 [options] <gitignore>')
    .command({
        command: '<gitignore>',
        description: 'gitignore input file(s)',
        type: 'string'
    })
    .demandCommand(min=1, minMsg='at least one gitignore file must be specified')
    .check((argv, options) => {
        const file_paths = argv._;
        file_paths.forEach(file_path => {
            if (!require('fs').existsSync(file_path)) {
                throw new Error(`gitignore file, ${file_path}, does not exist`);
            }
        });
        return true;
    })
    .option('verbose', { alias: 'v', type: 'boolean', default: false, description: 'Run with verbose logging'})
    .option('negate', { alias: 'n', type: 'boolean', default: false, description: 'Negate the list of ignore paths' })
    .option('seperator', { alias: 's', type: 'string', default: '|', description: 'String to seperate output globs' })
    .option('wrapper', { alias: 'w', type: 'string', default: '', description: 'String to specify what if any text to wrap the individual output' })
    .argv;

String.prototype.trimLeft = function(charlist) {
  if (charlist === undefined)
    charlist = "\s";
  return this.replace(new RegExp("^[" + charlist + "]+"), "");
};

String.prototype.trimRight = function(charlist) {
  if (charlist === undefined)
    charlist = "\s";
  return this.replace(new RegExp("[" + charlist + "]+$"), "");
};

function get_ignore_globs(gitignores, wrapper, seperator, negate, verbose) {
    let globs_str = '';
    for (let gitignore of gitignores) {
        const gitignore_globs = gitignore_to_glob(gitignore);
        gitignore_globs.forEach(glob => {
            if (verbose) {
                console.log('ignore: %s', negate ? glob : glob.trimLeft('!'));
            }
            let glob_str = '';
            if (negate) {
                glob_str = `${wrapper}${glob}${wrapper}`;
            } else {
                glob_str = `${wrapper}${glob.trimLeft('!')}${wrapper}`;
            }
            globs_str += glob_str + seperator;
        });
    }
    return globs_str.trimRight(seperator);
}

const main = function() {
    try {
        globs_str = get_ignore_globs(argv._, argv.wrapper, argv.seperator, argv.negate, argv.verbose);
        console.log(globs_str);
    } catch (err) {
        console.log((err));
    }
};

main();
