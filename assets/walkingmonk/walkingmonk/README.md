# Monk Scroller

A fixed bottom scroll-progress bar whose thumb is an animated monk:
he **walks** while the page scrolls, and settles into **meditation**
when it's still. You can also drag him left/right to scroll the page,
like a horizontal scrollbar handle.

## Files

```
monk-scroller.css     styles for the track + thumb
monk-scroller.js      self-initializing widget logic (vanilla JS, no deps)
images/
  walk1.svg / walk2.svg           walking animation frames
  meditate1.svg / meditate2.svg   meditating animation frames
demo.html              full working example with sample content
```

## Integrate into any page

1. Copy `monk-scroller.css`, `monk-scroller.js`, and the whole `images/`
   folder into your project, keeping them in the same relative location
   to each other (or update `imageBase`, see below).
2. Add to your `<head>`:
   ```html
   <link rel="stylesheet" href="monk-scroller.css">
   ```
3. Add just before `</body>`:
   ```html
   <script src="monk-scroller.js"></script>
   ```
4. That's it — the widget attaches itself automatically on page load.
   No other markup or setup required.

### Optional config

Set this *before* `monk-scroller.js` loads if your images live somewhere
else, or to tune timing:

```html
<script>
  window.MonkScrollerConfig = {
    imageBase: '/assets/monk/',   // default: 'images/'
    idleDelay: 700,               // ms of no scroll before he sits to meditate
    walkFrameMs: 140,             // walking animation speed
    meditateFrameMs: 650          // meditating animation speed
  };
</script>
<script src="monk-scroller.js"></script>
```

## Notes

- The bar reserves ~56px at the bottom of the viewport. Add
  `padding-bottom` to your `<body>` if content is being covered.
- Works with mouse, touch, and arrow-key input (thumb is focusable).
- Images are plain SVG — recolor by editing the `fill`/`stroke` hex
  values directly, or swap in your own art using the same filenames.
