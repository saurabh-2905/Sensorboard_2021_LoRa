
from metrics import hard_failure, gateway_failure

# hard_failure.eval("log_red2.pkl")
a,b = gateway_failure.eval("log_exp_gf1.pkl")

print(a,b)