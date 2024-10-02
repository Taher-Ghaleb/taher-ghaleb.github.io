library(data.table)
library(nnet)
library(lmtest)
library(AER)
library(car)
library(dplyr)
library(rstatix)
library(dunn.test)
#======== Multinomial Regression Models using Project-Level Factors (RQ1) =========
project_level_data <- read.csv("Data/project_level_data.csv", header = TRUE, sep=',', stringsAsFactors = T)

correlated_metrics <- c("build_counts", "build_jobs", "forks", "proj.building.freq.days")
categorical_variables   <- c("gh_repository_name", "lang", "quadrant")
dependent_variables <- c("quadrant")
independent_variables <- colnames(project_level_data)[!(colnames(project_level_data) %in% c("gh_repository_name", "median_duration", "breakage_ratio", "first_build", "last_build", dependent_variables, correlated_metrics))]

df <- project_level_data[, colnames(project_level_data) %in% c(dependent_variables,independent_variables)]
df[, !(colnames(df) %in% categorical_variables)] <- as.data.frame(lapply(df[, !(colnames(df) %in% categorical_variables)], function(x) as.numeric(x)))
data.frame.complete <- df[complete.cases(df),]
data.frame.complete$quadrant <- relevel(data.frame.complete$quadrant, ref='timely_passed')

frmla <- as.formula(paste("quadrant ~ ", paste(independent_variables, collapse= "+")))
multinom.model <- multinom(frmla, data = data.frame.complete, na.action = na.exclude)
coeftest(multinom.model)
step_model <- step(multinom.model, direction='both', trace=F)
Anova(step_model)

#======== Multinomial Regression Models using Quarter-Level Factors (RQ1) =========
quarter_level_data <- read.csv("Data/quarter_level_data.csv", header = TRUE, sep=',', stringsAsFactors = T)

for (Qid in 1:4) {
  df <- quarter_level_data[quarter_level_data$Qt_id == Qid,]
  df$Qt_id <- NULL

  correlated_metrics <- c("build_counts", "build_jobs", "forks")
  categorical_variables   <- c("gh_repository_name", "lang", "quadrant")
  dependent_variables <- c("quadrant")
  independent_variables <- colnames(df)[!(colnames(df) %in% c("gh_repository_name", "median_duration", "breakage_ratio", dependent_variables, correlated_metrics))]

  df <- df[, colnames(df) %in% c(dependent_variables,independent_variables)]

  df[, !(colnames(df) %in% categorical_variables)] <- as.data.frame(lapply(df[, !(colnames(df) %in% categorical_variables)], function(x) as.numeric(x)))
  df[,   colnames(df) %in% categorical_variables]  <- as.data.frame(lapply(df[,  colnames(df)  %in% categorical_variables] , function(x) factor(x)))
  data.frame.complete <- df[complete.cases(df),]
  data.frame.complete$quadrant <- relevel(data.frame.complete$quadrant, ref='timely_passed')

  frmla <- as.formula(paste("quadrant ~ ", paste(independent_variables, collapse= "+")))
  multinom.model <- multinom(frmla, data = data.frame.complete, na.action = na.exclude)
  print(Qid)
  coeftest(multinom.model)
  step_model <- step(multinom.model, direction='both', trace=F)
  Anova(step_model)
}

#======== Quadrants Analyses (RQ1) =========
quarter_level_data <- read.csv("Data/quarter_level_data.csv", header = TRUE, sep=',', stringsAsFactors = T)

q1_dur <- quarter_level_data[quarter_level_data$Qt_id == 1,]$median_duration
q2_dur <- quarter_level_data[quarter_level_data$Qt_id == 2,]$median_duration
q3_dur <- quarter_level_data[quarter_level_data$Qt_id == 3,]$median_duration
q4_dur <- quarter_level_data[quarter_level_data$Qt_id == 4,]$median_duration

q1_br <- quarter_level_data[quarter_level_data$Qt_id == 1,]$breakage_ratio
q2_br <- quarter_level_data[quarter_level_data$Qt_id == 2,]$breakage_ratio
q3_br <- quarter_level_data[quarter_level_data$Qt_id == 3,]$breakage_ratio
q4_br <- quarter_level_data[quarter_level_data$Qt_id == 4,]$breakage_ratio

quarter_level_data %>% group_by(Qt_id) %>% get_summary_stats(median_duration, type = "common")
quarter_level_data %>% group_by(Qt_id) %>% get_summary_stats(breakage_ratio, type = "common")

quarter_level_data %>% kruskal.test(median_duration~Qt_id)
quarter_level_data %>% kruskal.test(breakage_ratio~Qt_id)

kruskal.test(median_duration~Qt_id, quarter_level_data)
kruskal.test(breakage_ratio~Qt_id, quarter_level_data)

quarter_level_data %>% kruskal_effsize(median_duration~Qt_id)
quarter_level_data %>% kruskal_effsize(breakage_ratio~Qt_id)

dunn.test(list(q1_dur,q2_dur,q3_dur,q4_dur))
dunn.test(list(q1_br,q2_br,q3_br,q4_br))

projects_names <- c()
projects_num_quadrants <- c()
for (proj in unique(quarter_level_data$gh_repository_name)){
  quadrants <- quarter_level_data[quarter_level_data$gh_repository_name == proj,]$quadrant
  projects_names <- c(projects_names,proj)
  unique_quadrants <- length(unique(quadrants))
  
  projects_num_quadrants <- c(projects_num_quadrants,unique_quadrants)
}
length(projects_num_quadrants[projects_num_quadrants == 1])/588
length(projects_num_quadrants[projects_num_quadrants == 2])/588
length(projects_num_quadrants[projects_num_quadrants == 3])/588
length(projects_num_quadrants[projects_num_quadrants == 4])/588
