require 'jekyll'

puts "Loading Jekyll site..."
config = Jekyll.configuration({})
site = Jekyll::Site.new(config)

puts "Reading site..."
site.read

puts "\n" + "="*60
puts "Scanning for invalid permalinks"
puts "="*60

found = false

site.pages.each do |page|
  perm = page.data['permalink']
  if perm && !perm.is_a?(String)
    found = true
    puts "\n❌ INVALID PERMALINK IN PAGE:"
    puts "   File: #{page.path}"
    puts "   Type: #{perm.class}"
    puts "   Value: #{perm.inspect}"
    puts "   Permalink raw: #{page.data['permalink'].inspect}"
  end
end

site.posts.docs.each do |post|
  perm = post.data['permalink']
  if perm && !perm.is_a?(String)
    found = true
    puts "\n❌ INVALID PERMALINK IN POST:"
    puts "   File: #{post.path}"
    puts "   Type: #{perm.class}"
    puts "   Value: #{perm.inspect}"
  end
end

unless found
  puts "\n✓ No invalid permalinks found in pages or posts."
  puts "  The issue might be in a plugin or configuration."
end

puts "\n" + "="*60