def forward(...) = g(...)
def anonymous(*, **, &); g(*, **, &); end
def pattern(x); case x; in {name:}; name; end; end
def implicit; xs.map { it.to_s }; end
__END__
def fake; 2; end
