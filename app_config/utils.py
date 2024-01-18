def snake_to_camel_case(input_string):
    words = input_string.split('_')  # Assuming input_string is snake_case

    # word.capitalize() capitalizes the first letter, but lowercases all other letters in the word
    # this makes it so if we run the function twice on the word 'gs_outage_order', 
    # we get 'GsOutageOrder' the first time, but 'Gsoutageorder' the second time.
    # or even if we run it on an already camel-case string, like 'GsOutageOrder', we get 'Gsoutageorder' - it messes it up.
    # that's why we need to capitalize the first letter of each word manually
    return ''.join([f"{word[0].upper()}{word[1:]}" for word in words])
