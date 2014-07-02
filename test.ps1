$a = "hello world"
write $a
$dir = Get-Location
foreach ($subdir in $dir.GetDirectories())
{
	write $subdir;
}