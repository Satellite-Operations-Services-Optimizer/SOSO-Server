CREATE OR REPLACE FUNCTION set_default_name()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.name IS NULL THEN
        NEW.name := 'unnamed_' || TG_ARGV[0] || '_' || NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
