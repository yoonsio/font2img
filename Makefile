FONTFORGE  ?= fontforge
RESOLUTION ?= 1000
SIZE       ?= 500
OUT_DIR    ?= render

gen:
	$(FONTFORGE) -script font2img.py $(FONT) -r $(RESOLUTION) -s $(SIZE) -o $(OUT_DIR) -uln

clean:
	rm $(OUT_DIR)/*

