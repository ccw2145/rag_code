# Databricks notebook source
# DBTITLE 1,Install RAG Studio packages
# MAGIC %pip install databricks-rag-studio "mlflow@git+https://github.com/mlflow/mlflow.git@027c9c7b56265d8c50588b7f01c521296a1d3e2b"

# COMMAND ----------

# Before logging this chain using the driver notebook, you need to comment out this line.
# dbutils.library.restartPython() 

# COMMAND ----------

import mlflow
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnableLambda

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enable MLflow Tracing
# MAGIC
# MAGIC Enabling MLflow Tracing is required to:
# MAGIC - View the chain's trace visualization in this notebook
# MAGIC - Capture the chain's trace in production via Inference Tables
# MAGIC - Evaluate the chain via the Mosaic AI Evaluation Suite

# COMMAND ----------

mlflow.langchain.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chain helper functions

# COMMAND ----------

############
# Your chain must accept an array of OpenAI-formatted messages as a `messages` parameter. 
# Schema: https://docs.databricks.com/en/machine-learning/foundation-models/api-reference.html#chatmessage
# These helper functions help parse the `messages` array
############

# Return the string contents of the most recent message from the user
def extract_user_query_string(chat_messages_array):
    return chat_messages_array[-1]["content"]


# Return the chat history, which is is everything before the last question
def extract_chat_history(chat_messages_array):
    return chat_messages_array[:-1]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameterized Hello World chain

# COMMAND ----------

# MAGIC %md
# MAGIC ### Define the parameters 

# COMMAND ----------

# You can use any key:value pairs as parameters.
# The parameters can be loaded from a dict or from a YAML file
# When logging your model, this configuration can be overridden to experiment with different settings to improve quality

config_dict = {"sample_param": "this is the sample parameter that can be changed! this could be a prompt, a retrieval setting, or ..."}
model_config = mlflow.models.ModelConfig(development_config=config_dict)

# Example for loading from a YAML
# config_file = "configs/2_hello_world_config.yaml"
# model_config = mlflow.models.ModelConfig(development_config=config_file)

# COMMAND ----------

# DBTITLE 1,Hello World Model
############
# Fake model for this hello world example.
############
def fake_model(input):
    return f"Config: {model_config.get('sample_param')}.  You asked `{input.get('user_query')}`. Conversation history: {input.get('chat_history')}"


############
# Parameterized chain example
############
# RAG Studio requires the chain to return a string value.
chain = (
    {
        "user_query": itemgetter("messages")
        | RunnableLambda(extract_user_query_string),
        "chat_history": itemgetter("messages") | RunnableLambda(extract_chat_history),
    }
    | RunnableLambda(fake_model)
    | StrOutputParser()
)


# COMMAND ----------

# MAGIC %md
# MAGIC ## Test the chain locally

# COMMAND ----------

# This is the same input your chain's REST API will accept.
question = {
    "messages": [
        {
            "role": "user",
            "content": "question 1",
        },
        {
            "role": "assistant",
            "content": "answer 1",
        },
        {
            "role": "user",
            "content": "new question!!",
        },
    ]
}

# Uncomment this line to test the chain locally
# Private Preview workaround: We suggest commenting this line out before you log the model.  This is not strictly necessary but doing so will prevent additional MLflow traces from being show when calling mlflow.langchain.log_model(...).

# chain.invoke(question)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tell MLflow logging where to find your chain.
# MAGIC
# MAGIC `mlflow.models.set_model(model=...)` function specifies the LangChain chain to use for evaluation and deployment.  This is required to log this chain to MLflow with `mlflow.langchain.log_model(...)`.

# COMMAND ----------

mlflow.models.set_model(model=chain)
