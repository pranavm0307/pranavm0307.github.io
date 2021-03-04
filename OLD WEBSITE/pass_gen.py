import string
import random  



s2=string.ascii_lowercase
##print(s2)
s3=string.ascii_uppercase
##print(s3)
s4=string.digits
##print(s4)


s9=string.punctuation

paslen=int(input("Enter length of Password\n"))

s=[]
s.extend(list(s2))
s.extend(list(s3))
s.extend(list(s4))
s.extend(list(s9))

random.shuffle(s)
print("".join(s[0:paslen]))
