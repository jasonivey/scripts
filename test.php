#!/usr/bin/php -q
<?php
if(!defined("SUPPRESS_LOCALE_HEADERS")) {
    define("SUPPRESS_LOCALE_HEADERS", true);
}

function test_conversion($file_name1, $file_name2, $verbose) {
    $segment1 = get_legacy_segment($file_name1, $verbose);
    $segment2 = get_legacy_segment($file_name2, $verbose);
    if ($segment1 == $segment2) {
        echo "SUCCESS: The converted JSON is equivelant\n";
    } else {
        echo "FAILURE: The converted JSON is not equivelant\n";
    }
}

function get_legacy_segment($file_name, $verbose) {
    if ($verbose) {
        echo "File name: $file_name\n";
    }
    $json_data = file_get_contents($file_name);
    $segment = json_decode($json_data, true);
    unset($json_data);

    if (is_legacy_segment($segment)) {
        echo "$file_name is a legacy JSON file -- nothing to do\n";
        if ($verbose) {
            $json_str = json_encode($segment, JSON_PRETTY_PRINT);
            echo "$file_name:\n$json_str\n\n";
        }
        return $segment;
    } else {
        echo "$file_name is a new JSON file -- need to convert\n";
        $new_segment = create_legacy_segment($segment);
        if ($verbose) {
            $new_segment_json = json_encode($new_segment, JSON_PRETTY_PRINT);
            echo "$file_name:\n$new_segment_json\n\n";
        }
        return $new_segment;
    }
}

function is_legacy_segment($segment)
{
    return !isset($segment['segments']['dates']);
}

function create_legacy_segment($segment)
{
    $variables = array();
    $dates = array();
    foreach ($segment['segments'] as $key => $value) {
        if ($key === "variables") {
            foreach ($value as $variable_key => $variable_value) {
                $variables[$variable_key] = $variable_value;
            }
        } else if ($key === "dates") {
            $dates = $value;
        }
    }
    $updated_segment = array();
    $updated_segment['rsid'] = $segment['rsid'];
    $updated_segment['segments'] = array();
    foreach ($dates as $date) {
        $updated_segment['segments'][$date] = $variables;
    }
    return $updated_segment;
}

function print_usage() {
    echo "test.php <file1.json> <file2.json> [-v|--verbose]\n";
    exit();
}

if ($argc < 3) {
    echo "ERROR: too few arguments\n";
    print_usage();
}

$verbose = false;
$file_name1 = NULL;
$file_name2 = NULL;

foreach (array_slice($argv, 1) as $arg) {
    //echo "arg: $arg\n";
    if (substr($arg, 0, 3) === "--v" || substr($arg, 0, 2) === "-v") {
        $verbose = true;
    } else if (file_exists($arg)) {
        if (is_null($file_name1)) {
            $file_name1 = $arg;
        } else {
            $file_name2 = $arg;
        }
    }
}

if (is_null($file_name1) || is_null($file_name2)) {
    echo "ERROR: must specify two JSON files\n";
    print_usage();
}

test_conversion($file_name1, $file_name2, $verbose);

?>
