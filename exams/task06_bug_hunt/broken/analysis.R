library(dplyr)
library(fixest)

y <- read.csv("../raw/outcomes.csv")
x <- read.csv("../raw/covariates.csv")

# BUGS ARE INTENTIONAL
x <- x %>% arrange(firm_id, year)
d <- left_join(y, x, by=c("firm_id","year"))
d <- d %>% filter(age > 18)
d$log_sales <- log(d$sales)
d <- d %>% filter(!is.na(baseline_score))
d <- d %>% mutate(lag_y = lag(outcome))

m <- feols(outcome ~ treated_post + mediator + baseline_score + lag_y,
           data=d,
           vcov="hetero")
write.csv(data.frame(estimate=coef(m)[1], std_error=se(m)[1], n_obs=nobs(m)), "results.csv", row.names=FALSE)
