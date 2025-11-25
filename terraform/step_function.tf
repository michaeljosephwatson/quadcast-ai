# IAM Role for Step Function Execution
resource "aws_iam_role" "step_function_role" {
  name = "c20-quadcast-episode-transcription-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-episode-transcription-step-function-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy to allow Step Function to invoke Lambda and Glue
resource "aws_iam_role_policy" "step_function_lambda_policy" {
  name = "c20-quadcast-episode-transcription-step-function-lambda-policy"
  role = aws_iam_role.step_function_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.daily_pipeline.arn,
          aws_lambda_function.count_episodes.arn,
          aws_lambda_function.transcribe.arn,
          aws_lambda_function.analysis.arn,
          aws_lambda_function.vector_embedding.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartCrawler",
          "glue:GetCrawler"
        ]
        Resource = [
          aws_glue_crawler.quadcast_transcripts.arn
        ]
      }
    ]
  })
}

# Step Function Definition
resource "aws_sfn_state_machine" "episode_transcription_workflow" {
  name       = "c20-quadcast-episode-transcription-workflow"
  role_arn   = aws_iam_role.step_function_role.arn
  definition = jsonencode({
    Comment = "Complete podcast episode processing workflow: discovery, transcription, and summarization"
    StartAt = "RunDailyPipeline"
    States = {
      # Step 1: Discover new episodes
      RunDailyPipeline = {
        Type     = "Task"
        Resource = aws_lambda_function.daily_pipeline.arn
        Next     = "CountUntranscribedEpisodes"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "WorkflowFailed"
        }]
      }

      # Step 2: Count how many episodes need transcription
      CountUntranscribedEpisodes = {
        Type     = "Task"
        Resource = aws_lambda_function.count_episodes.arn
        ResultPath = "$.countResult"
        Next     = "CheckIfTranscriptionNeeded"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "WorkflowFailed"
        }]
      }

      # Step 3: Check if there are episodes to transcribe
      CheckIfTranscriptionNeeded = {
        Type = "Choice"
        Choices = [{
          Variable      = "$.countResult.body"
          StringMatches = "*\"count\":0*"
          Next          = "NoWorkToDo"
        }]
        Default = "ParseCountResult"
      }

      # Parse the count from the JSON body
      ParseCountResult = {
        Type       = "Pass"
        Parameters = {
          "countObj.$" = "States.StringToJson($.countResult.body)"
        }
        ResultPath = "$.parsedCount"
        Next       = "GenerateTranscriptionRange"
      }

      # Generate array for Map state [0, 1, 2, ..., count-1]
      GenerateTranscriptionRange = {
        Type = "Pass"
        Parameters = {
          "count.$"  = "$.parsedCount.countObj.count"
          "range.$"  = "States.ArrayRange(0, $.parsedCount.countObj.count, 1)"
        }
        ResultPath = "$.transcription"
        Next       = "TranscribeEpisodesInParallel"
      }

      # Step 4: Transcribe all episodes in parallel
      TranscribeEpisodesInParallel = {
        Type         = "Map"
        ItemsPath    = "$.transcription.range"
        MaxConcurrency = 10
        ResultPath   = "$.transcriptionResults"
        Iterator = {
          StartAt = "TranscribeEpisode"
          States = {
            TranscribeEpisode = {
              Type     = "Task"
              Resource = aws_lambda_function.transcribe.arn
              End      = true
              Retry = [{
                ErrorEquals     = ["States.ALL"]
                IntervalSeconds = 2
                MaxAttempts     = 2
                BackoffRate     = 2.0
              }]
              Catch = [{
                ErrorEquals = ["States.ALL"]
                ResultPath  = "$.error"
                Next        = "TranscriptionFailed"
              }]
            }
            TranscriptionFailed = {
              Type = "Pass"
              Result = {
                status = "failed"
              }
              End = true
            }
          }
        }
        Next = "ProcessTranscriptions"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "WorkflowFailed"
        }]
      }

      # Step 5: Process transcriptions (summarize and vector embedding in parallel)
      ProcessTranscriptions = {
        Type = "Parallel"
        Branches = [
          {
            StartAt = "SummarizeTranscribedEpisodes"
            States = {
              SummarizeTranscribedEpisodes = {
                Type         = "Map"
                ItemsPath    = "$.transcriptionResults"
                MaxConcurrency = 10
                ResultPath   = "$.summarizationResults"
                Iterator = {
                  StartAt = "ParseTranscriptionBodyForSummary"
                  States = {
                    ParseTranscriptionBodyForSummary = {
                      Type       = "Pass"
                      Parameters = {
                        "transcriptionData.$" = "States.StringToJson($.body)"
                      }
                      ResultPath = "$.parsed"
                      Next       = "CheckTranscriptionSuccessForSummary"
                    }

                    CheckTranscriptionSuccessForSummary = {
                      Type = "Choice"
                      Choices = [{
                        Variable     = "$.parsed.transcriptionData.status"
                        StringEquals = "success"
                        Next         = "SummarizeEpisode"
                      }]
                      Default = "SkipSummarization"
                    }

                    SummarizeEpisode = {
                      Type     = "Task"
                      Resource = aws_lambda_function.analysis.arn
                      Parameters = {
                        "episode_id.$"        = "$.parsed.transcriptionData.episode_id"
                        "podcast_id.$"        = "$.parsed.transcriptionData.podcast_id"
                        "transcript_s3_key.$" = "$.parsed.transcriptionData.transcript_s3_key"
                      }
                      End = true
                      Retry = [{
                        ErrorEquals     = ["States.ALL"]
                        IntervalSeconds = 2
                        MaxAttempts     = 2
                        BackoffRate     = 2.0
                      }]
                      Catch = [{
                        ErrorEquals = ["States.ALL"]
                        ResultPath  = "$.error"
                        Next        = "SummarizationFailed"
                      }]
                    }

                    SkipSummarization = {
                      Type = "Pass"
                      Result = {
                        status  = "skipped"
                        message = "Transcription failed, skipping summarization"
                      }
                      End = true
                    }

                    SummarizationFailed = {
                      Type = "Pass"
                      Result = {
                        status = "failed"
                      }
                      End = true
                    }
                  }
                }
                End = true
              }
            }
          },
          {
            StartAt = "VectorEmbedTranscribedEpisodes"
            States = {
              VectorEmbedTranscribedEpisodes = {
                Type         = "Map"
                ItemsPath    = "$.transcriptionResults"
                MaxConcurrency = 10
                ResultPath   = "$.vectorEmbeddingResults"
                Iterator = {
                  StartAt = "ParseTranscriptionBodyForVector"
                  States = {
                    ParseTranscriptionBodyForVector = {
                      Type       = "Pass"
                      Parameters = {
                        "transcriptionData.$" = "States.StringToJson($.body)"
                      }
                      ResultPath = "$.parsed"
                      Next       = "CheckTranscriptionSuccessForVector"
                    }

                    CheckTranscriptionSuccessForVector = {
                      Type = "Choice"
                      Choices = [{
                        Variable     = "$.parsed.transcriptionData.status"
                        StringEquals = "success"
                        Next         = "VectorEmbedEpisode"
                      }]
                      Default = "SkipVectorEmbedding"
                    }

                    VectorEmbedEpisode = {
                      Type     = "Task"
                      Resource = aws_lambda_function.vector_embedding.arn
                      Parameters = {
                        "episode_id.$" = "$.parsed.transcriptionData.episode_id"
                        "podcast_id.$" = "$.parsed.transcriptionData.podcast_id"
                      }
                      End = true
                      Retry = [{
                        ErrorEquals     = ["States.ALL"]
                        IntervalSeconds = 2
                        MaxAttempts     = 2
                        BackoffRate     = 2.0
                      }]
                      Catch = [{
                        ErrorEquals = ["States.ALL"]
                        ResultPath  = "$.error"
                        Next        = "VectorEmbeddingFailed"
                      }]
                    }

                    SkipVectorEmbedding = {
                      Type = "Pass"
                      Result = {
                        status  = "skipped"
                        message = "Transcription failed, skipping vector embedding"
                      }
                      End = true
                    }

                    VectorEmbeddingFailed = {
                      Type = "Pass"
                      Result = {
                        status = "failed"
                      }
                      End = true
                    }
                  }
                }
                End = true
              }
            }
          }
        ]
        Next = "RunGlueCrawler"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "WorkflowFailed"
        }]
      }

      # Step 6: Run Glue Crawler to update schema
      RunGlueCrawler = {
        Type     = "Task"
        Resource = "arn:aws:states:::aws-sdk:glue:startCrawler"
        Parameters = {
          Name = aws_glue_crawler.quadcast_transcripts.name
        }
        Next = "WorkflowComplete"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.crawlerError"
          Next        = "WorkflowComplete"
        }]
      }

      # TODO: Re-enable summarization steps when llm_summarise Lambda is deployed
      # # Step 5: Count episodes again to see how many need summarization
      # CountTranscribedEpisodes = {
      #   Type     = "Task"
      #   Resource = aws_lambda_function.count_episodes.arn
      #   ResultPath = "$.summarizationCountResult"
      #   Next     = "CheckIfSummarizationNeeded"
      #   Catch = [{
      #     ErrorEquals = ["States.ALL"]
      #     Next        = "WorkflowFailed"
      #   }]
      # }

      # # Step 6: Check if there are transcripts to summarize
      # CheckIfSummarizationNeeded = {
      #   Type = "Choice"
      #   Choices = [{
      #     Variable      = "$.summarizationCountResult.body"
      #     StringMatches = "*\"count\":0*"
      #     Next          = "WorkflowComplete"
      #   }]
      #   Default = "ParseSummarizationCount"
      # }

      # # Parse summarization count
      # ParseSummarizationCount = {
      #   Type       = "Pass"
      #   Parameters = {
      #     "count.$" = "States.StringToJson($.summarizationCountResult.body).count"
      #   }
      #   ResultPath = "$.parsedSummarizationCount"
      #   Next       = "GenerateSummarizationRange"
      # }

      # # Generate array for summarization Map state
      # GenerateSummarizationRange = {
      #   Type = "Pass"
      #   Parameters = {
      #     "count.$"  = "$.parsedSummarizationCount.count"
      #     "range.$"  = "States.ArrayRange(0, $.parsedSummarizationCount.count, 1)"
      #   }
      #   ResultPath = "$.summarization"
      #   Next       = "SummarizeEpisodesInParallel"
      # }

      # # Step 7: Summarize all episodes in parallel
      # SummarizeEpisodesInParallel = {
      #   Type         = "Map"
      #   ItemsPath    = "$.summarization.range"
      #   MaxConcurrency = 10
      #   ResultPath   = "$.summarizationResults"
      #   Iterator = {
      #     StartAt = "SummarizeEpisode"
      #     States = {
      #       SummarizeEpisode = {
      #         Type     = "Task"
      #         Resource = aws_lambda_function.llm_summarise.arn
      #         End      = true
      #         Retry = [{
      #           ErrorEquals     = ["States.ALL"]
      #           IntervalSeconds = 2
      #           MaxAttempts     = 2
      #           BackoffRate     = 2.0
      #         }]
      #         Catch = [{
      #           ErrorEquals = ["States.ALL"]
      #           ResultPath  = "$.error"
      #           Next        = "SummarizationFailed"
      #         }]
      #       }
      #       SummarizationFailed = {
      #         Type = "Pass"
      #         Result = {
      #           status = "failed"
      #         }
      #         End = true
      #       }
      #     }
      #   }
      #   Next = "WorkflowComplete"
      #   Catch = [{
      #     ErrorEquals = ["States.ALL"]
      #     Next        = "WorkflowFailed"
      #   }]
      # }

      # Success states
      NoWorkToDo = {
        Type = "Pass"
        Result = {
          status  = "success"
          message = "No episodes to process"
        }
        End = true
      }

      WorkflowComplete = {
        Type = "Pass"
        Result = {
          status  = "success"
          message = "All episodes processed successfully"
        }
        End = true
      }

      # Failure state
      WorkflowFailed = {
        Type = "Pass"
        Result = {
          status  = "failed"
          message = "Workflow encountered an error"
        }
        End = true
      }
    }
  })

  tags = {
    Name        = "c20-quadcast-episode-transcription-workflow"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
