#!/usr/bin/env ruby
require 'd:/scripts/Utils.rb'

if __FILE__ == $0
    sandbox = FindSandbox(Dir.getwd)
    filename = File.join(sandbox, "ws", "RecoveryAccess", "Dev", "RPAM", "RPAMTest", "RPAM_Store.dat")
    File.delete(filename) if File.exists? filename
    filename = File.join("C:", "Documents and Settings", "All Users", "Application Data", "Symantec", "RPAM", "RPAM_Cache.dat")
    File.delete(filename) if File.exists? filename
end
