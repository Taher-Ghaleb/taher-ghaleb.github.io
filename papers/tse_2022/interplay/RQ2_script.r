library(data.table)
library(nnet)
library(lmtest)
library(AER)
library(car)
#======== Multinomial Regression Model using Build-Level Metrics (RQ1) =========
build_level_data <- read.csv("Data/build_level_data.csv", header = TRUE, sep=',')

unwanted_metrics <- c("tr_build_id", "gh_repository_name", "gh_lang", "gh_build_started_at", "git_trigger_commit", "build_status", "build_duration_seconds")
correlated_metrics <- c("config_lines_added", "config_lines_deleted", "author_experience_num_commits", "gh_diff_src_files", "num_jobs_removed")
dependent_variables <- c("build_quadrant")
independent_variables <- colnames(build_level_data)[!(colnames(build_level_data) %in% c(unwanted_metrics,dependent_variables, correlated_metrics))]
categorical_variables <- c("build_quadrant", "weekday_weekend", "build_day_night", "commit_day_of_week", "commit_day_night", "gh_is_pr", "caching", "fast_finish", "gh_by_core_team_member", "dist", "oses", "sudo", "docker")

df <- build_level_data[, (colnames(build_level_data) %in% c(dependent_variables,independent_variables))]
df[, !(colnames(df) %in% categorical_variables)] <- as.data.frame(lapply(df[, !(colnames(df) %in% categorical_variables)], function(x) as.numeric(x)))
df[,   colnames(df) %in% categorical_variables]  <- as.data.frame(lapply(df[,  colnames(df)  %in% categorical_variables] , function(x) factor(x)))
df$commit_day_night[df$commit_day_night == ''] <- NA
df$commit_day_night[df$build_day_night == ''] <- NA
data.frame.complete <- df[complete.cases(df),]

data.frame.complete$build_quadrant <- relevel(data.frame.complete$build_quadrant, ref='timely_passed')
data.frame.complete$commit_day_night <- relevel(data.frame.complete$commit_day_night, ref='day')
data.frame.complete$oses <- relevel(data.frame.complete$oses, ref='linux')
data.frame.complete$dist <- relevel(data.frame.complete$dist, ref='default')

frmla <- as.formula(paste("build_quadrant ~ ", paste(independent_variables, collapse= "+")))
multinom.model <- multinom(frmla, data = data.frame.complete, na.action = na.exclude)
coeftest(multinom.model)
step_model <- step(multinom.model, direction='both')
Anova(step_model)
