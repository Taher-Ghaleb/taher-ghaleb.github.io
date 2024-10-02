library(data.table)
library(lmtest)
library(car)
library(lme4)
library(MuMIn)
#======== Switching Models (RQ3) =========
run_glmm_switching_model <- function(df, indp, model_name, ref_level, npar=TRUE, print=FALSE){
  df$obs <- as.factor(1:nrow(df))
  df_complete <- df[complete.cases(df),]
  
  df_complete$build_quadrant <- factor(df_complete$build_quadrant)
  df_complete$build_quadrant <- relevel(df_complete$build_quadrant, ref=ref_level)
  
  start.time <- Sys.time()
  start.time
  
  ###--- Mixed-effects Logistic model ---###
  frmla.glmm.model <- as.formula(paste('build_quadrant ~ ', paste(c(colnames(df_complete)[ colnames(df_complete) %in% c(indp)], "(1 | gh_repository_name)", "(1 | obs)") , collapse= "+")))
  glmm.model <- NULL
  glmm.model <- glmer(frmla.glmm.model, data = df_complete, na.action = na.exclude, family = binomial(link=logit), control=glmerControl(optimizer=c("Nelder_Mead", "bobyqa")), nAGQ = 0)

  smry <- as.data.frame(summary(glmm.model)$coefficients)
  names(smry)[names(smry) == 'Pr(>|z|)'] <- 'P.Value'
  smry <- smry[order(row.names(smry)),]
  
  anov <- as.data.frame(Anova(glmm.model, type=3))
  anov$Df <- NULL
  anov$Chisq_ratio <- round(anov$Chisq/sum(anov$Chisq[-1])*100, 2)
  anov$Chisq_ratio[1] <- ''
  anov <- anov[order(row.names(anov)),]
  names(anov)[names(anov) == 'Pr(>Chisq)'] <- 'P.Value'
  anov$Signif <- ifelse(anov$P.Value <= 0.001, '***', ifelse(anov$P.Value > 0.001 & anov$P.Value <= 0.01, '**', ifelse(anov$P.Value > 0.01 & anov$P.Value <= 0.05, '*', ifelse(anov$P.Value > 0.05 & anov$P.Value <= 0.1, '.', ' '))))
  anov$P.Value <- as.character(ifelse(anov$P.Value < 2.2e-16, '< 2.2e-16', anov$P.Value))
  anov$Chisq <- round(anov$Chisq, 3)
  
  r_sqr <- r.squaredGLMM(glmm.model)
  df_complete$prob <- predict(glmm.model, type=c('response'))
  frmla.auc <- as.formula(paste('build_quadrant ~ prob'))
  AUC <- pROC::roc(frmla.auc, data = df_complete)
  AUC <- AUC$auc[1]
  
  end.time <- Sys.time()
  time.taken <- end.time - start.time
  time.taken
  
  anov <- rbind(c('', '', '', '', ''), anov)
  rownames(anov)[1] <- '--------------------------------'
  anov <- rbind(R2_conditional=c(round(r_sqr[[2]], 3), '', '', '', ''), anov)
  anov <- rbind(R2_marginal=c(round(r_sqr[[1]], 3), '', '', '', ''), anov)
  anov <- rbind(AUC=c(round(AUC, 3), '', '', '', ''), anov)
  anov <- rbind(c('', '', '', '', ''), anov)
  rownames(anov)[1] <- '---------------'
  anov <- rbind(Model=c(model_name, '', '', '', ''), anov)
  smry <- rbind(c('', '', '', '', ''), smry)
  rownames(smry)[1] <- '---------------'
  smry <- rbind(Model=c(model_name, '', '', '', ''), smry)
  
  return(list(smry, anov, AUC, time.taken))
} 

project_level_data <- read.csv("Data/project_level_data.csv", header = TRUE, sep=',')
build_level_data <- read.csv("Data/build_level_data.csv", header = TRUE, sep=',')

unwanted_metrics <- c("tr_build_id", "gh_lang", "gh_build_started_at", "git_trigger_commit")
correlated_metrics <- c("config_lines_added", "config_lines_deleted", "author_experience_num_commits", "gh_diff_src_files", "num_jobs_removed")
dependent_variables <- c("build_quadrant", "gh_repository_name", "build_status", "build_duration_seconds")
independent_variables <- colnames(build_level_data)[!(colnames(build_level_data) %in% c(unwanted_metrics,dependent_variables, correlated_metrics))]
categorical_variables <- c("gh_repository_name", "build_quadrant", "build_status", "weekday_weekend", "build_day_night", "commit_day_of_week", "commit_day_night", "gh_is_pr", "caching", "fast_finish", "gh_by_core_team_member", "dist", "oses", "sudo", "docker")

df <- build_level_data[, (colnames(build_level_data) %in% c(dependent_variables,independent_variables))]
df[, !(colnames(df) %in% categorical_variables)] <- as.data.frame(lapply(df[, !(colnames(df) %in% categorical_variables)], function(x) as.numeric(x)))
df[,   colnames(df) %in% categorical_variables]  <- as.data.frame(lapply(df[,  colnames(df)  %in% categorical_variables] , function(x) factor(x)))
df$commit_day_night[df$commit_day_night == ''] <- NA
df$commit_day_night[df$build_day_night == ''] <- NA
data.frame.complete <- df[complete.cases(df),]

overall_median_duration <- median(project_level_data$median_duration)*60

# --- One direction (six models) --- #

#From Long/Broken  To  Timely/Passed
LB_to_TP <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_broken", "timely_passed"),]
LB_to_TP <- LB_to_TP[(LB_to_TP$build_quadrant=="timely_passed" & LB_to_TP$build_duration_seconds <= overall_median_duration & LB_to_TP$build_status == "passed") | (LB_to_TP$build_quadrant=="long_broken" & LB_to_TP$build_duration_seconds > overall_median_duration & LB_to_TP$build_status %in% c("errored", "failed")),]
LB_to_TP_result <- run_glmm_switching_model(LB_to_TP, independent_variables, "LB => TP", 'long_broken')

#From Long/Broken  To  Long/Passed
LB_to_LP <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_broken", "long_passed"),]
LB_to_LP <- LB_to_LP[(LB_to_LP$build_quadrant=="long_passed" & LB_to_LP$build_duration_seconds > overall_median_duration & LB_to_LP$build_status == "passed") | (LB_to_LP$build_quadrant=="long_broken" & LB_to_LP$build_duration_seconds > overall_median_duration & LB_to_LP$build_status %in% c("errored", "failed")),]
LB_to_LP_result <- run_glmm_switching_model(LB_to_LP, independent_variables, "LB => LP", 'long_broken')

#From Long/Broken  To  Timely/Broken
LB_to_TB <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_broken", "timely_broken"),]
LB_to_TB <- LB_to_TB[(LB_to_TB$build_quadrant=="timely_broken" & LB_to_TB$build_duration_seconds <= overall_median_duration & LB_to_TB$build_status %in% c("errored", "failed")) | (LB_to_TB$build_quadrant=="long_broken" & LB_to_TB$build_duration_seconds > overall_median_duration & LB_to_TB$build_status %in% c("errored", "failed")),]
LB_to_TB_result <- run_glmm_switching_model(LB_to_TB, independent_variables, "LB => TB", 'long_broken')

#From Long/Passed  To  Timely/Passed
LP_to_TP <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_passed", "timely_passed"),]
LP_to_TP <- LP_to_TP[(LP_to_TP$build_quadrant=="timely_passed" & LP_to_TP$build_duration_seconds <= overall_median_duration & LP_to_TP$build_status == "passed") | (LP_to_TP$build_quadrant=="long_passed" & LP_to_TP$build_duration_seconds > overall_median_duration & LP_to_TP$build_status == "passed"),]
LP_to_TP_result <- run_glmm_switching_model(LP_to_TP, independent_variables, "LP => TP", 'long_passed')

#From Long/Passed  To  Timely/Broken
LP_to_TB <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_passed", "timely_broken"),]
LP_to_TB <- LP_to_TB[(LP_to_TB$build_quadrant=="timely_broken" & LP_to_TB$build_duration_seconds <= overall_median_duration & LP_to_TB$build_status %in% c("errored", "failed")) | (LP_to_TB$build_quadrant=="long_passed" & LP_to_TB$build_duration_seconds > overall_median_duration & LP_to_TB$build_status == "passed"),]
LP_to_TB_result <- run_glmm_switching_model(LP_to_TB, independent_variables, "LP => TB", 'long_passed')

#From Timely/Broken  To  Timely/Passed
TB_to_TP <- data.frame.complete[data.frame.complete$build_quadrant %in% c("timely_broken", "timely_passed"),]
TB_to_TP <- TB_to_TP[(TB_to_TP$build_quadrant=="timely_passed" & TB_to_TP$build_duration_seconds <= overall_median_duration & TB_to_TP$build_status == "passed") | (TB_to_TP$build_quadrant=="timely_broken" & TB_to_TP$build_duration_seconds <= overall_median_duration & TB_to_TP$build_status %in% c("errored", "failed")),]
TB_to_TP_result <- run_glmm_switching_model(TB_to_TP, independent_variables, "TB => TP", 'timely_broken')

# --- Other direction (six models) --- #
#From Timely/Passed To Long/Broken  
TP_to_LB <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_broken", "timely_passed"),]
TP_to_LB <- TP_to_LB[(TP_to_LB$build_quadrant=="timely_passed" & TP_to_LB$build_duration_seconds <= overall_median_duration & TP_to_LB$build_status == "passed") | (TP_to_LB$build_quadrant=="long_broken" & TP_to_LB$build_duration_seconds > overall_median_duration & TP_to_LB$build_status %in% c("errored", "failed")),]
TP_to_LB_result <- run_glmm_switching_model(TP_to_LB, independent_variables, "TP => LB", 'timely_passed')

#From Long/Passed To Long/Broken  
LP_to_LB <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_broken", "long_passed"),]
LP_to_LB <- LP_to_LB[(LP_to_LB$build_quadrant=="long_passed" & LP_to_LB$build_duration_seconds > overall_median_duration & LP_to_LB$build_status == "passed") | (LP_to_LB$build_quadrant=="long_broken" & LP_to_LB$build_duration_seconds > overall_median_duration & LP_to_LB$build_status %in% c("errored", "failed")),]
LP_to_LB_result <- run_glmm_switching_model(LP_to_LB, independent_variables, "LP => LB", 'long_passed')

#From Timely/Broken To Long/Broken
TB_to_LB <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_broken", "timely_broken"),]
TB_to_LB <- TB_to_LB[(TB_to_LB$build_quadrant=="timely_broken" & TB_to_LB$build_duration_seconds <= overall_median_duration & TB_to_LB$build_status %in% c("errored", "failed")) | (TB_to_LB$build_quadrant=="long_broken" & TB_to_LB$build_duration_seconds > overall_median_duration & TB_to_LB$build_status %in% c("errored", "failed")),]
TB_to_LB_result <- run_glmm_switching_model(TB_to_LB, independent_variables, "TB => LB", 'timely_broken')

#From Timely/Passed To Long/Passed
TP_to_LP <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_passed", "timely_passed"),]
TP_to_LP <- TP_to_LP[(TP_to_LP$build_quadrant=="timely_passed" & TP_to_LP$build_duration_seconds <= overall_median_duration & TP_to_LP$build_status == "passed") | (TP_to_LP$build_quadrant=="long_passed" & TP_to_LP$build_duration_seconds > overall_median_duration & TP_to_LP$build_status == "passed"),]
TP_to_LP_result <- run_glmm_switching_model(TP_to_LP, independent_variables, "TP => LP", 'timely_passed')

#From Timely/Broken To Long/Passed
TB_to_LP <- data.frame.complete[data.frame.complete$build_quadrant %in% c("long_passed", "timely_broken"),]
TB_to_LP <- TB_to_LP[(TB_to_LP$build_quadrant=="timely_broken" & TB_to_LP$build_duration_seconds <= overall_median_duration & TB_to_LP$build_status %in% c("errored", "failed")) | (TB_to_LP$build_quadrant=="long_passed" & TB_to_LP$build_duration_seconds > overall_median_duration & TB_to_LP$build_status == "passed"),]
TB_to_LP_result <- run_glmm_switching_model(TB_to_LP, independent_variables, "TB => LP", 'timely_broken')

#From Timely/Passed To Timely/Broken
TP_to_TB <- data.frame.complete[data.frame.complete$build_quadrant %in% c("timely_broken", "timely_passed"),]
TP_to_TB <- TP_to_TB[(TP_to_TB$build_quadrant=="timely_passed" & TP_to_TB$build_duration_seconds <= overall_median_duration & TP_to_TB$build_status == "passed") | (TP_to_TB$build_quadrant=="timely_broken" & TP_to_TB$build_duration_seconds <= overall_median_duration & TP_to_TB$build_status %in% c("errored", "failed")),]
TP_to_TB_result <- run_glmm_switching_model(TP_to_TB, independent_variables, "TP => TB", 'timely_passed')

# --- --- #

write.csv(cbind(LB_to_TP_result[[1]],'',LB_to_LP_result[[1]],'',LB_to_TB_result[[1]],'',LP_to_TP_result[[1]],'',LP_to_TB_result[[1]],'',TB_to_TP_result[[1]],'',TP_to_LB_result[[1]],'',LP_to_LB_result[[1]],'',TB_to_LB_result[[1]],'',TP_to_LP_result[[1]],'',TB_to_LP_result[[1]],'',TP_to_TB_result[[1]]), paste0('RQ3_results/Summary.csv'))
write.csv(cbind(LB_to_TP_result[[2]],'',LB_to_LP_result[[2]],'',LB_to_TB_result[[2]],'',LP_to_TP_result[[2]],'',LP_to_TB_result[[2]],'',TB_to_TP_result[[2]],'',TP_to_LB_result[[2]],'',LP_to_LB_result[[2]],'',TB_to_LB_result[[2]],'',TP_to_LP_result[[2]],'',TB_to_LP_result[[2]],'',TP_to_TB_result[[2]]), paste0('RQ3_results/Anova.csv'))
