import openai
openai.api_key = "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"
model_engine = "text-davinci-002"
prompt = "print 'Hello, World!' in C++"
completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        stop='\@',
        temperature=0.5,
    )

print(completions.choices[0].text)