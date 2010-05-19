from tasks import *

result = add.delay(8, 8)
print result.wait() # wait for and return the result
