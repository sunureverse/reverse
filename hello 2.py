string_a = "{}".format(10)

print(string_a)
print(type(string_a))

format_a = "{}만원".format(50000)
format_b = "파이썬 열공하여 첫연봉 {}만원 만들기".format(5000)
format_c = "{} {} {} ".format(3000, 4000, 5000)
format_d = "{} {} {} ".format(1, "문자열", True)

print(format_a)
print(format_b)
print(type(format_c))
print(type(format_d))

output_a = "{:d}".format(52)
output_b = "{:5d}".format(52)
output_c = "{:10d}".format(52)
output_d = "{:05d}".format(52)
output_e = "{:05d}".format(-52)

print(output_a)
print(output_b)
print(output_c)
print(output_d)
print(output_e)

output_f = "{:+5d}".format(+52)
output_g = "{:+5d}".format(-52)
output_h = "{:=+5d}".format(52)
output_i = "{:=+5d}".format(-52)

print(output_f)
print(output_g)
print(output_h)
print(output_i)