library(data.table)
library(lmtest)
library(car)
library(lme4)
library(MuMIn)
#======== Statistical modeling (GLM) of state-switching switching over time -- Within-project=========
build_level_data <- read.csv("Data/build_level_data.csv", header = TRUE, sep=',')
switching_patterns_overtime  <- read.csv("RQ4_results/switching_patterns_and_sub_patterns_overtime.csv", header = TRUE, sep=',')
merged.df.with.switching_patterns <- merge(build_level_data, switching_patterns_overtime[,-1])
merged.df.with.switching_patterns$pattern <- gsub("-->", "=>", merged.df.with.switching_patterns$pattern, fixed = TRUE)
merged.df.with.switching_patterns$sub_pattern <- gsub("-->", "=>", merged.df.with.switching_patterns$sub_pattern, fixed = TRUE)
merged.df.with.switching_patterns$sub_pattern_details <- gsub("-->", "=>", merged.df.with.switching_patterns$sub_pattern_details, fixed = TRUE)

unwanted_metrics <- c("tr_build_id", "gh_lang", "gh_build_started_at", "git_trigger_commit")
correlated_metrics <- c("config_lines_added", "config_lines_deleted", "author_experience_num_commits", "gh_diff_src_files", "num_jobs_removed")
dependent_variables <- c("build_quadrant", "gh_repository_name", "build_status", "build_duration_seconds")
independent_variables <- colnames(build_level_data)[!(colnames(build_level_data) %in% c(unwanted_metrics,dependent_variables, correlated_metrics))]
categorical_variables <- c("gh_repository_name", "build_quadrant", "build_status", "weekday_weekend", "build_day_night", "commit_day_of_week", "commit_day_night", "gh_is_pr", "caching", "fast_finish", "gh_by_core_team_member", "dist", "oses", "sudo", "docker")
trends_metrics <- c("pattern", "sub_pattern", "sub_pattern_details")

within_project_patterns_models_results <- data.frame(matrix(ncol = 8, nrow = 0))
colnames(within_project_patterns_models_results) <- c('project.name', 'switching.pattern', 'metric.name', 'Chisq_ratio', 'Signif', 'Direction', 'P.Value', 'Chisq')

is.steady <- ""
project_count = 0
for(project.name in unique(merged.df.with.switching_patterns$gh_repository_name)){
  project_count = project_count + 1
  print(paste(project_count, '-', project.name))
  project.df <- merged.df.with.switching_patterns[merged.df.with.switching_patterns$gh_repository_name == project.name,]
  project.df_complete <- project.df[complete.cases(project.df),]
  switching_pattern <- as.character(project.df$sub_pattern_details[1])
  switching_pattern_list <- unlist(strsplit(switching_pattern, " => "))
  is.steady <- ifelse(project.df$sub_pattern_details[1] %in% c('timely_passed => timely_passed => timely_passed => timely_passed', 'timely_broken => timely_broken => timely_broken => timely_broken', 'long_passed => long_passed => long_passed => long_passed', 'long_broken => long_broken => long_broken => long_broken'), T, F)
  if(!is.steady & nrow(project.df_complete) > 0){
    by <- as.integer(nrow(project.df)/4)
    quarters_periods <- list(1:by,(by+1):(2*by),(2*by+1):(3*by),(3*by+1):(nrow(project.df)))
    for(i in 1:3) {
      this_period_df <- project.df[quarters_periods[[i]],]
      this_period_df$switching_label <- switching_pattern_list[i]
      next_period_df <- project.df[quarters_periods[[i+1]],]
      next_period_df$switching_label <- switching_pattern_list[i+1]
      period_df <- rbind(this_period_df, next_period_df)
      period_df$switching_label <- factor(period_df$switching_label)
      period_df$switching_label <- relevel(period_df$switching_label, ref=switching_pattern_list[i])
      period_df_complete <- period_df[complete.cases(period_df),]
      switching_pattern <- paste0(switching_pattern_list[i], '->', switching_pattern_list[i+1])
      
      selected_metrics <- c()
      for(metric in independent_variables){
        if(metric %in% categorical_variables){
          period_df_complete[, metric] <- factor(period_df_complete[, metric])
          selected_values <- period_df_complete[, metric][!is.na(period_df_complete[, metric]) & period_df_complete[, metric]!= '']
          num_levels <- length(unique(selected_values))
          if(num_levels > 1){
            selected_metrics <- c(selected_metrics, metric)
          }
        }else{
          period_df_complete[, metric] <- as.numeric(period_df_complete[, metric])
          selected_metrics <- c(selected_metrics, metric)
        }
      }
      
      if(nrow(period_df_complete) > 0){
        if(switching_pattern %in% c('long_broken->timely_passed',
                                    'long_passed->timely_passed',
                                    'timely_broken->timely_passed',
                                    'long_broken->long_passed',
                                    'timely_broken->long_passed',
                                    'long_broken->timely_broken')
        ){
          ### GLM ###
          frmla.glm.model <- as.formula(paste("switching_label ~ ", paste(selected_metrics, collapse= "+")))
          glm.model <- NULL
          glm.model <- glm(frmla.glm.model, data = period_df_complete, na.action = na.exclude, family = binomial(link=logit))
          smry <- as.data.frame(summary(glm.model)$coefficients)
          smry$metric.name <- rownames(smry)
          smry$metric.name <- ifelse(smry$metric.name == 'weekday_weekendweekend', 'weekday_weekend', ifelse(smry$metric.name == 'build_day_nightnight', 'build_day_night', ifelse(smry$metric.name == 'commit_day_nightnight', 'commit_day_night', ifelse(smry$metric.name == 'gh_by_core_team_member1', 'gh_by_core_team_member', ifelse(smry$metric.name == 'gh_is_pr1', 'gh_is_pr', ifelse(smry$metric.name == 'caching1', 'caching', ifelse(smry$metric.name == 'fast_finish1', 'fast_finish', ifelse(smry$metric.name == 'disttrusty', 'dist', ifelse(smry$metric.name == 'oseslinux+osx', 'oses', ifelse(smry$metric.name == 'osesosx', 'oses', ifelse(smry$metric.name == 'sudo1', 'sudo', ifelse(smry$metric.name == 'docke1', 'docker', smry$metric.name))))))))))))
          estimates <- smry[smry$metric.name != '(Intercept)', c('metric.name', 'Estimate')]
          anov <- as.data.frame(Anova(glm.model))
          names(anov)[names(anov) == 'LR Chisq'] <- 'Chisq'
          names(anov)[names(anov) == 'Pr(>Chisq)'] <- 'P.Value'
          anov$Df <- NULL
          anov$project.name <- project.name
          anov$metric.name <- rownames(anov)
          sum_Chisq <- sum(anov$Chisq[!is.na(anov$Chisq)])
          anov$Chisq_ratio <- round(anov$Chisq/sum_Chisq*100, 2)
          anov$Signif <- ifelse(anov$P.Value <= 0.001, '***', ifelse(anov$P.Value > 0.001 & anov$P.Value <= 0.01, '**', ifelse(anov$P.Value > 0.01 & anov$P.Value <= 0.05, '*', ifelse(anov$P.Value > 0.05 & anov$P.Value <= 0.1, '.', ' '))))
          anov$P.Value <- as.character(ifelse(anov$P.Value < 2.2e-16, '< 2.2e-16', anov$P.Value))
          anov$Chisq <- round(anov$Chisq, 3)
          anov_only_significant <- anov[anov$Signif %in% c('*', '**', '***'),]
          if(nrow(anov_only_significant) > 0){
            anov_only_significant_with_estimates <- NULL
            anov_only_significant_with_estimates <- merge(anov_only_significant, estimates)
            anov_only_significant_with_estimates$switching.pattern <- switching_pattern
            anov_only_significant_with_direction <- anov_only_significant_with_estimates[, c('project.name', 'switching.pattern', 'metric.name', 'Chisq_ratio', 'Signif', 'Estimate', 'P.Value', 'Chisq')]
            anov_only_significant_with_direction <- anov_only_significant_with_direction[order(anov_only_significant_with_direction$Chisq, decreasing = T),]
            
            within_project_patterns_models_results <- rbind(within_project_patterns_models_results, anov_only_significant_with_direction)
          }
        }
      }
    }
  }
}
unique(within_project_patterns_models_results$project.name)
write.csv(within_project_patterns_models_results, "RQ4_results/within_project_patterns_models_results_.csv", row.names = F)
