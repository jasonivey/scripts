package main

import "fmt"
import "path/filepath"
import "os"
import "flag"
//import "errors"

func visit(path string, f os.FileInfo, err error) error {
    fmt.Printf("Visited: %s\n", path)
    return nil
}

func main() {
    flag.Parse()
    root := flag.Arg(0)
    fileList := []string{}
    //err := filepath.Walk(root, visit)
    err := filepath.Walk(root, func(path string, f os.FileInfo, err error) error {
        if err == nil {
            fileList = append(fileList, path)
            fmt.Print(".")
        } else {
            fmt.Printf("filepath.Walk encountered %v.\n", err)
        }
        return nil
    })
    fmt.Println()
    for _, file := range fileList {
        fmt.Println(file)
    }
    fmt.Printf("filepath.Walk() returned %v\n", err)
}
