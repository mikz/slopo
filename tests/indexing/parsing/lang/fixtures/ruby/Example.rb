class Calculator
  def inc(x) = x + 1
  def self.increment(x) = x + 1
end
adder = ->(x) { x + 1 }
callback = proc { |x| x + 1 }
describe "X" do
  it("works") { check }
end
define_method(:foo) { 1 }
attr_reader :x
x = 1
