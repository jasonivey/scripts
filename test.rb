
class MegaGreeter
    attr_accessor :names
    
    #Create the object
    def initialize(names = "World")
        @names = names
    end
    
    # Say hi to everybody
    def say_hi
        if @names.nil?
            puts "..."
        elsif @names.respond_to?("each")
            @names.each do |name|
                puts "Hello #{name}!"
            end
        else
            puts "Hello #{@names}!"
        end
    end
    
    #Say bye to everybody
    def say_bye
        if @names.nil?
            puts "..."
        elsif @names.respond_to?("join")
            puts "Goodbye #{@names.join(", ")}. Come back soon!"
        else
            puts "Goodbye #{@names}. Come back soon!"
        end
    end
end

def FindSandbox(dir)
    while(dir != File.join(dir, ".."))
        if File.exists?(File.join(dir, 'sandbox.txt'))
            return dir
        else
            dir = File.expand_path(File.join(dir, ".."))
        end
    end
    puts 'Unable to find a sandbox'
    return dir
end

if __FILE__ == $0
    sandbox = FindSandbox(Dir.getwd)
    File.delete(File.join(sandbox, "ws", "RecoveryAccess", "Dev", "RPAM", "RPAMTest", "RPAM_Store.dat"))
    File.delete(File.join("C:", "Documents and Settings", "All Users", "Application Data", "Symantec", "RPAM", "RPAM_Cache.dat"))
end
