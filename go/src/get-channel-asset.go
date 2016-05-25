package main

import "errors"
import "fmt"
import "flag"
import "net/http"
import "encoding/json"
import "io/ioutil"
import "os"
import "github.com/nu7hatch/gouuid"
import "strings"

var verbose bool

//const hexPattern = "^(urn\\:uuid\\:)?\\{?([a-z0-9]{8})-([a-z0-9]{4})-" +
//                   "([1-5][a-z0-9]{3})-([a-z0-9]{4})-([a-z0-9]{12})\\}?$"

//var re = regexp.MustCompile(hexPattern)

//http://bbtv.qa.movetv.com/cms/publish3/channel/qvt/4/a519cb94154e4b9282a6122bb61a6ed2/today.qvt

func GetRemoteJson(url string) (map[string]interface{}, error) {
    if verbose {
        fmt.Println("fetching", url)
    }
    response, err := http.Get(url)
    if err != nil {
        return nil, err
    }

    defer response.Body.Close()
    contents, err := ioutil.ReadAll(response.Body)
    if err != nil {
        return nil, err
    }

    if verbose {
        //fmt.Println("contents:", string(contents))
    }

    var dat map[string]interface{}
    if err = json.Unmarshal([]byte(contents), &dat); err != nil {
        return nil, err
    }

    if verbose {
        //fmt.Printf("content:\n%s\n", dat)
    }
    return dat, nil
}

func GetContainerId(channel_id string, cms string) (int, error) {
    url := fmt.Sprintf("%s/cms/publish3/channel/qvt/4/%s/today.qvt", cms, channel_id)
    data, err := GetRemoteJson(url)
    if err != nil {
        return -1, err
    }
    container_id, ok := data["container_id"]
    if !ok {
        return -1, errors.New(fmt.Sprintf("The channel %s did not have a container id", channel_id))
    }
    if verbose {
        fmt.Println("container_id:", container_id)
    }
    fmt.Println("type", (container_id).type)
    if str, ok := container_id.(int); !ok {
        return -1, errors.New("")
    } else {
        return str, nil
    }
    //return string(container_id), nil
}

//type UuidFlag uuid.UUID

//func (i *uuid.UUID) String() string {
//    return i.String()
//}

//func (i *uuid.UUID) Set(value string) error {
//    if len(value) == 32 {
//        value_str := value[:8] + "-"
//        value_str += value[8:12] + "-"
//        value_str += value[12:16] + "-"
//        value_str += value[16:20] + "-"
//        value_str += value[20:]
//        value = value_str
//    }
//    u, err := uuid.ParseHex(value)
//    if err != nil {
//        return err
//    }
//    *i = u
//    return nil
//}

func ParseArgs() (string, string, error) {
    flag.BoolVar(&verbose, "verbose", false, "output verbose information")
    channelPtr := flag.String("channel", "", "channel identifier (uuid)")
    //var channel_id uuid.UUID
    //flag.Var(&channel_id, "channel", "channel identifier (uuid)")
    cmsPtr := flag.String("cms", "bbtv.qa.movetv.com", "host name of cms server (i.e. bbtv.qa.movetv.com)")
    flag.Parse()

    if len(*channelPtr) == 32 {
        channel_str := *channelPtr
        channel := channel_str[:8] + "-"
        channel += channel_str[8:12] + "-"
        channel += channel_str[12:16] + "-"
        channel += channel_str[16:20] + "-"
        channel += channel_str[20:]
        *channelPtr = channel
    }
    channel_id, err := uuid.ParseHex(*channelPtr)
    if err != nil {
        //return nil, nil, err
        return "", "", err
    }
    if verbose {
        fmt.Println("channel:", channel_id)
        fmt.Println("cms:", "http://" + *cmsPtr)
        fmt.Println("verbose:", verbose)
    }
    cms := strings.TrimRight("http://" + *cmsPtr, "/")
    return channel_id.String(), cms, nil
}

func main() {
    channel, cms, err := ParseArgs()
    if err != nil {
        fmt.Println("error:", err)
        os.Exit(1)
    }

    channel = strings.Replace(channel, "-", "", -1)
    //container_id, err := GetContainerId(channel, cms)
    _, err = GetContainerId(channel, cms)
    if err != nil {
        fmt.Println("error:", err)
        os.Exit(1)
    }
}
