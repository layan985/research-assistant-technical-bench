clear all
import delimited "../raw/outcomes.csv", clear
merge m:m firm_id year using "../raw/covariates.csv"
keep if _merge==3
drop _merge
keep if age>18
gen log_sales = log(sales)
sort year firm_id
by year: gen lag_y = outcome[_n-1]
reg outcome treated_post mediator baseline_score lag_y i.firm_id, robust
outreg2 using results.csv, replace csv
