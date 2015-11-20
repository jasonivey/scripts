package main

import (
	"bufio"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

func main() {
	inFilename, outFilename, err := filenamesFromCommandLine()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	infile, outFile := os.Stdin, os.Stdout
	if inFilename != "" {
		if inFile, err = os.Open(inFilename); err != nil {
			log.Fatal(err)
		}
		defer infile.Close()
	}
	if outFilename != "" {
		if outFile, err = os.Create(outFilename); err != nil {
			log.Fatal(err)
		}
		defer outFile.Close()
	}
	if err = americanise(infile, outfile); err != nil {
		log.Fatal(err)
	}
}

func filenamesFromCommandLine() (inFilename string, outFilename string, err error) {
	if len(os.Args) > 1 && (os.Args[1] == "-h" || os.Args[1] == "--help") {
		err = fmt.Errorf("usage: %s [<]infile.txt [<]outfile.txt", filepath.Base(os.Args[0]))
		return "", "", err
	}
	if len(os.Args) > 1 {
		inFilename = os.Args[1]
		if len(os.Args) > 2 {
			outFilename = os.Args[2]
		}
	}
	if inFilename != "" && inFilename == outFilename {
		log.Fatal("won't overwrite the infile")
	}
	return inFilename, outFilename, nil
}
