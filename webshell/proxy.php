<?php
ini_set("display_errors", 1);
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    print("curl_init\n");
    var_dump(function_exists("curl_init"));
    print("fsockopen\n");
    var_dump(function_exists("fsockopen"));
    print("file_get_contents\n");
    var_dump(function_exists("file_get_contents"));
    exit("stinger php!");
}
function my_socket_post($url, $data)
{
    $url = parse_url($url);
    if (empty ($url ['scheme']) || $url ['scheme'] != 'http') {
        die ("Error: Only HTTP request are supported !");
    }
    $host = $url ['host'];
    $port = $url ['port'];
    $path = isset ($url ['path']) ? $url ['path'] : '/';
    $fp = fsockopen($host, $port, $errno, $errstr, 3);
    if ($fp) {
        // send the request headers:
        $length = strlen($data);
        $POST = <<<HEADER
POST {$path} HTTP/1.1
Host: {$host}:$port
Accept: */*
Content-Length: {$length}
Content-Type: application/x-www-form-urlencoded\r\n
{$data}
HEADER;
        fwrite($fp, $POST);
        $result = '';
        $result .= fread($fp, 10240);
//        while (!feof($fp)) {
//            $result .= fread($fp, 4096);
//        }
    } else {
        return array(
            'status' => 'error',
            'error' => "$errstr ($errno)"
        );
    }
    // close the socket connection:
    fclose($fp);
    // split the result header from the content
    $result = explode("\r\n\r\n", $result, 2);
    print_r(isset ($result [1]) ? $result [1] : '');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $post_arg = file_get_contents("php://input");
    $RemoteServer = $_POST['Remoteserver'];
    $Endpoint = $_POST['Endpoint'];
    if (function_exists('curl_init')) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_arg);
        curl_setopt($ch, CURLOPT_URL, $RemoteServer . $Endpoint);
        curl_exec($ch);
        curl_close($ch);
    } elseif (function_exists("curl_init")) {
        $url = $RemoteServer . $Endpoint;
        my_socket_post($url, $post_arg);
    } else {
        exit("stinger php error!");
    }
}
?>