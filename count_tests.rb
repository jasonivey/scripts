#!/usr/bin/env ruby

def FindSandbox(dir)
  while(dir != File.join(dir, ".."))
      if File.exists?(File.join(dir, 'sandbox.txt'))
          return dir
      else
          dir = File.expand_path(File.join(dir, ".."))
      end
  end
  puts 'ERROR: Unable to find a sandbox'
  exit 1
end


if __FILE__ == $0
  testrunners = Dir.glob(File.join("**", "TestRunner.exe"))
  count = 0
  for test in testrunners
    puts "\n#{test}"
    result = %x["#{File.join(Dir.getwd, test)}", "-info"]
    puts result.split.length
    count += result.split.length
    #i = system("#{File.join(Dir.getwd, test)}", "-info")
    #puts i
  end
  puts "Count: #{count}"
  #Kernel.exec 
end